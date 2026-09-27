import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Restore SchoolManagerPro database and media "
        "from a timestamped backup."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "backup",
            help=(
                "Path to the backup folder containing "
                "database.sqlite3 and media."
            ),
        )

        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm that the live system should be restored.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError(
                "Restore not executed. "
                "Re-run the command with --confirm "
                "after verifying the backup path."
            )

        backup_dir = Path(options["backup"]).resolve()

        backup_database = backup_dir / "database.sqlite3"
        backup_media = backup_dir / "media"

        database_name = settings.DATABASES["default"]["NAME"]
        media_root = Path(settings.MEDIA_ROOT).resolve()

        if not database_name:
            raise CommandError(
                "The configured database name is empty."
            )

        database_path = Path(database_name).resolve()

        if not backup_dir.is_dir():
            raise CommandError(
                f"Backup directory was not found: {backup_dir}"
            )

        if not backup_database.is_file():
            raise CommandError(
                f"Backup database was not found: {backup_database}"
            )

        if not backup_media.is_dir():
            raise CommandError(
                f"Backup media directory was not found: {backup_media}"
            )

        if backup_database == database_path:
            raise CommandError(
                "The backup database is the live database. "
                "Restore was refused."
            )

        # =========================================================
        # VERIFY SOURCE BACKUP DATABASE
        # =========================================================

        try:
            connection = sqlite3.connect(
                str(backup_database)
            )

            try:
                integrity = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
            finally:
                connection.close()

        except Exception as exc:
            raise CommandError(
                f"Could not verify backup database: {exc}"
            ) from exc

        if integrity != "ok":
            raise CommandError(
                "Backup database failed integrity check: "
                f"{integrity}"
            )

        # =========================================================
        # INVENTORY SOURCE MEDIA
        # =========================================================

        backup_media_files = [
            path
            for path in backup_media.rglob("*")
            if path.is_file()
        ]

        backup_media_size = sum(
            path.stat().st_size
            for path in backup_media_files
        )

        # =========================================================
        # CREATE PRE-RESTORE SAFETY BACKUP
        # =========================================================

        safety_root = Path(settings.BASE_DIR) / "backups"

        timestamp = datetime.now().strftime(
            "%Y-%m-%d_%H%M%S_%f"
        )

        safety_dir = safety_root / (
            f"pre_restore_{timestamp}"
        )

        safety_database = safety_dir / "database.sqlite3"
        safety_media = safety_dir / "media"

        safety_dir.mkdir(
            parents=True,
            exist_ok=False,
        )

        try:
            if not database_path.exists():
                raise CommandError(
                    f"Live database was not found: {database_path}"
                )

            source = sqlite3.connect(
                str(database_path)
            )

            destination = sqlite3.connect(
                str(safety_database)
            )

            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()

            if media_root.exists():
                shutil.copytree(
                    media_root,
                    safety_media,
                )
            else:
                safety_media.mkdir(
                    parents=True,
                    exist_ok=True,
                )

        except CommandError:
            shutil.rmtree(
                safety_dir,
                ignore_errors=True,
            )
            raise

        except Exception as exc:
            shutil.rmtree(
                safety_dir,
                ignore_errors=True,
            )

            raise CommandError(
                "Could not create pre-restore safety backup: "
                f"{exc}"
            ) from exc

        # =========================================================
        # PREPARE RESTORE FILES BEFORE TOUCHING LIVE SYSTEM
        # =========================================================

        temporary_database = database_path.with_name(
            f"{database_path.stem}"
            f".restore_tmp_{timestamp}"
            f"{database_path.suffix}"
        )

        temporary_media = media_root.parent / (
            f"{media_root.name}"
            f".restore_tmp_{timestamp}"
        )

        try:
            # -----------------------------------------------------
            # Prepare temporary database.
            # -----------------------------------------------------

            shutil.copy2(
                backup_database,
                temporary_database,
            )

            connection = sqlite3.connect(
                str(temporary_database)
            )

            try:
                temporary_integrity = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
            finally:
                connection.close()

            if temporary_integrity != "ok":
                raise CommandError(
                    "Temporary restored database failed "
                    f"integrity check: {temporary_integrity}"
                )

            # -----------------------------------------------------
            # Prepare temporary media.
            # -----------------------------------------------------

            if temporary_media.exists():
                shutil.rmtree(
                    temporary_media,
                    ignore_errors=True,
                )

            shutil.copytree(
                backup_media,
                temporary_media,
            )

            temporary_media_files = [
                path
                for path in temporary_media.rglob("*")
                if path.is_file()
            ]

            temporary_media_size = sum(
                path.stat().st_size
                for path in temporary_media_files
            )

            if (
                len(temporary_media_files)
                != len(backup_media_files)
            ):
                raise CommandError(
                    "Temporary media verification failed: "
                    "file count does not match the backup."
                )

            if temporary_media_size != backup_media_size:
                raise CommandError(
                    "Temporary media verification failed: "
                    "total media size does not match the backup."
                )

        except CommandError:
            if temporary_database.exists():
                temporary_database.unlink()

            if temporary_media.exists():
                shutil.rmtree(
                    temporary_media,
                    ignore_errors=True,
                )

            raise

        except Exception as exc:
            if temporary_database.exists():
                temporary_database.unlink()

            if temporary_media.exists():
                shutil.rmtree(
                    temporary_media,
                    ignore_errors=True,
                )

            raise CommandError(
                "Could not prepare restore files. "
                f"Safety backup: {safety_dir}. "
                f"Error: {exc}"
            ) from exc

        # =========================================================
        # REPLACE LIVE SYSTEM
        # =========================================================

        database_replaced = False
        media_replaced = False

        try:
            # Close Django database connections before touching
            # the live SQLite database.
            from django.db import connections

            connections.close_all()

            # -----------------------------------------------------
            # Replace database.
            # -----------------------------------------------------

            database_path.unlink()

            temporary_database.replace(
                database_path
            )

            database_replaced = True

            # -----------------------------------------------------
            # Replace media.
            # -----------------------------------------------------

            if media_root.exists():
                shutil.rmtree(
                    media_root
                )

            temporary_media.replace(
                media_root
            )

            media_replaced = True

        except Exception as exc:
            # -----------------------------------------------------
            # Attempt database rollback.
            # -----------------------------------------------------

            rollback_errors = []

            try:
                from django.db import connections

                connections.close_all()
            except Exception as rollback_exc:
                rollback_errors.append(
                    f"Could not close Django connections: "
                    f"{rollback_exc}"
                )

            if database_replaced:
                try:
                    if database_path.exists():
                        database_path.unlink()

                    shutil.copy2(
                        safety_database,
                        database_path,
                    )
                except Exception as rollback_exc:
                    rollback_errors.append(
                        "Database rollback failed: "
                        f"{rollback_exc}"
                    )

            # -----------------------------------------------------
            # Attempt media rollback.
            # -----------------------------------------------------

            if media_replaced:
                try:
                    if media_root.exists():
                        shutil.rmtree(
                            media_root
                        )

                    if safety_media.exists():
                        shutil.copytree(
                            safety_media,
                            media_root,
                        )
                except Exception as rollback_exc:
                    rollback_errors.append(
                        "Media rollback failed: "
                        f"{rollback_exc}"
                    )

            if temporary_database.exists():
                temporary_database.unlink()

            if temporary_media.exists():
                shutil.rmtree(
                    temporary_media,
                    ignore_errors=True,
                )

            message = (
                "Restore failed. "
                f"Safety backup: {safety_dir}. "
                f"Original error: {exc}"
            )

            if rollback_errors:
                message += (
                    " Rollback warnings: "
                    + " | ".join(rollback_errors)
                )

            raise CommandError(message) from exc

        # =========================================================
        # FINAL VERIFICATION
        # =========================================================

        try:
            connection = sqlite3.connect(
                str(database_path)
            )

            try:
                final_integrity = connection.execute(
                    "PRAGMA integrity_check"
                ).fetchone()[0]
            finally:
                connection.close()

        except Exception as exc:
            raise CommandError(
                "Restore completed, but the restored database "
                f"could not be verified: {exc}. "
                f"Safety backup: {safety_dir}"
            ) from exc

        if final_integrity != "ok":
            raise CommandError(
                "Restore completed, but the restored database "
                f"failed integrity check: {final_integrity}. "
                f"Safety backup: {safety_dir}"
            )

        # ---------------------------------------------------------
        # Verify restored media.
        # ---------------------------------------------------------

        final_media_files = [
            path
            for path in media_root.rglob("*")
            if path.is_file()
        ]

        final_media_size = sum(
            path.stat().st_size
            for path in final_media_files
        )

        if len(final_media_files) != len(
            backup_media_files
        ):
            raise CommandError(
                "Restore completed, but final media verification "
                "failed: file count does not match the backup. "
                f"Safety backup: {safety_dir}"
            )

        if final_media_size != backup_media_size:
            raise CommandError(
                "Restore completed, but final media verification "
                "failed: total media size does not match the backup. "
                f"Safety backup: {safety_dir}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "SchoolManagerPro restore completed successfully."
            )
        )

        self.stdout.write(
            f"Restored from: {backup_dir}"
        )

        self.stdout.write(
            f"Database integrity: {final_integrity}"
        )

        self.stdout.write(
            f"Media files: {len(final_media_files)}"
        )

        self.stdout.write(
            "Media size: "
            f"{final_media_size / (1024 * 1024):.2f} MB"
        )

        self.stdout.write(
            f"Pre-restore safety backup: {safety_dir}"
        )