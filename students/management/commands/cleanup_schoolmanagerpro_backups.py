import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = (
        "Remove old SchoolManagerPro backups while preserving "
        "the configured number of recent normal backups."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--keep",
            type=int,
            default=14,
            help=(
                "Number of most recent normal backups to keep. "
                "Default: 14."
            ),
        )

        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Confirm that old backups may be deleted.",
        )

    def handle(self, *args, **options):
        keep = options["keep"]

        if keep < 1:
            raise CommandError(
                "The --keep value must be at least 1."
            )

        if not options["confirm"]:
            raise CommandError(
                "Cleanup not executed. "
                "Re-run the command with --confirm "
                "after reviewing the retention setting."
            )

        backup_root = (
            Path(settings.BASE_DIR) / "backups"
        )

        if not backup_root.exists():
            self.stdout.write(
                self.style.WARNING(
                    "Backup directory does not exist. "
                    "Nothing to clean."
                )
            )
            return

        normal_backups = []

        for path in backup_root.iterdir():
            if not path.is_dir():
                continue

            # Normal backups use:
            # YYYY-MM-DD_HHMMSS
            try:
                from datetime import datetime

                datetime.strptime(
                    path.name,
                    "%Y-%m-%d_%H%M%S",
                )
            except ValueError:
                continue

            normal_backups.append(path)

        normal_backups.sort(
            key=lambda path: path.name,
            reverse=True,
        )

        backups_to_delete = normal_backups[keep:]

        if not backups_to_delete:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No old backups to remove. "
                    f"Keeping {len(normal_backups)} normal backup(s)."
                )
            )
            return

        self.stdout.write(
            f"Normal backups found: {len(normal_backups)}"
        )

        self.stdout.write(
            f"Backups to keep: {keep}"
        )

        self.stdout.write(
            f"Backups to delete: {len(backups_to_delete)}"
        )

        for backup in backups_to_delete:
            try:
                shutil.rmtree(backup)
            except Exception as exc:
                raise CommandError(
                    f"Could not delete backup {backup}: {exc}"
                ) from exc

            self.stdout.write(
                f"Deleted: {backup}"
            )

        self.stdout.write(
            self.style.SUCCESS(
                "SchoolManagerPro backup cleanup completed."
            )
        )