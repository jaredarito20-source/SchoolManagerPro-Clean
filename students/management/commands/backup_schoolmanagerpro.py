import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a timestamped SchoolManagerPro database and media backup."

    def handle(self, *args, **options):
        database_name = settings.DATABASES["default"]["NAME"]
        media_root = Path(settings.MEDIA_ROOT)

        if not database_name:
            raise CommandError("The configured database name is empty.")

        database_path = Path(database_name)

        if not database_path.exists():
            raise CommandError(
                f"Database file was not found: {database_path}"
            )

        backup_root = Path(settings.BASE_DIR) / "backups"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_dir = backup_root / timestamp
        backup_database = backup_dir / "database.sqlite3"
        backup_media = backup_dir / "media"

        backup_dir.mkdir(parents=True, exist_ok=False)

        try:
            source = sqlite3.connect(str(database_path))
            destination = sqlite3.connect(str(backup_database))

            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()

            if media_root.exists():
                shutil.copytree(media_root, backup_media)
            else:
                backup_media.mkdir(parents=True)

        except Exception as exc:
            shutil.rmtree(backup_dir, ignore_errors=True)
            raise CommandError(
                f"Backup failed: {exc}"
            ) from exc

        database_size = backup_database.stat().st_size

        media_files = [
            path
            for path in backup_media.rglob("*")
            if path.is_file()
        ]

        media_size = sum(
            path.stat().st_size
            for path in media_files
        )

        self.stdout.write(
            self.style.SUCCESS(
                "SchoolManagerPro backup completed successfully."
            )
        )
        self.stdout.write(f"Backup: {backup_dir}")
        self.stdout.write(
            f"Database: {database_size / (1024 * 1024):.2f} MB"
        )
        self.stdout.write(
            f"Media files: {len(media_files)}"
        )
        self.stdout.write(
            f"Media size: {media_size / (1024 * 1024):.2f} MB"
        )
