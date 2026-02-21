#!/usr/bin/env python3
"""Download kitten media from Google Drive and rebuild kittens.json.

Expected Google Drive structure:
  пометы/
    помёт_O14(18.08.25)/
      fOriana(n blue solid polidactyl)/
        <photos/videos>
      мама/
      папа/
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    from google.auth.transport.requests import Request
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload
except ImportError:
    print(
        "Missing dependency. Install with:\n"
        "  pip install google-api-python-client google-auth-oauthlib google-auth-httplib2",
        file=sys.stderr,
    )
    raise

try:
    from PIL import Image, ImageOps
except ImportError:
    print(
        "Missing dependency. Install with:\n"
        "  pip install Pillow",
        file=sys.stderr,
    )
    raise


FOLDER_MIME = "application/vnd.google-apps.folder"
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
DEFAULT_ROOT_FOLDER_NAME = "\u043f\u043e\u043c\u0435\u0442\u044b"
DEFAULT_SKIP_FOLDER_NAMES = ("\u043c\u0430\u043c\u0430", "\u043f\u0430\u043f\u0430")
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic", ".heif"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv"}
INVALID_FILE_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
DATE_PATTERN = re.compile(r"(?<!\d)\d{1,2}[./-]\d{1,2}[./-]\d{2,4}(?!\d)")
THUMB_DIR_NAME = "thumbs"
DEFAULT_THUMB_SIZE = 900
DEFAULT_MAX_IMAGE_EDGE = 1600
DEFAULT_JPEG_QUALITY = 86


@dataclass(frozen=True)
class DriveFile:
    id: str
    name: str
    mime_type: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync kittens media from Google Drive to local website folders."
    )
    parser.add_argument(
        "--root-folder-id",
        help="Google Drive folder ID for the root folder (preferred for reliability).",
    )
    parser.add_argument(
        "--root-folder-name",
        default=DEFAULT_ROOT_FOLDER_NAME,
        help=f'Root folder name if --root-folder-id is not provided (default: "{DEFAULT_ROOT_FOLDER_NAME}").',
    )
    parser.add_argument(
        "--output-dir",
        default="public/cats/kittens",
        help="Local directory where kitten folders are stored.",
    )
    parser.add_argument(
        "--json-output",
        default="kittens.json",
        help="Path to output kittens JSON file.",
    )
    parser.add_argument(
        "--credentials-file",
        default="drive_client_secret.json",
        help="OAuth client secret JSON file path.",
    )
    parser.add_argument(
        "--token-file",
        default="drive_token.json",
        help="OAuth token cache file path.",
    )
    parser.add_argument(
        "--service-account-file",
        default="",
        help="Optional service account JSON file path. If provided, OAuth is skipped.",
    )
    parser.add_argument(
        "--skip-folder",
        action="append",
        default=list(DEFAULT_SKIP_FOLDER_NAMES),
        help="Folder name to ignore inside each litter. Can be used multiple times.",
    )
    parser.add_argument(
        "--skip-videos",
        action="store_true",
        help="Do not download video files.",
    )
    parser.add_argument(
        "--wipe-output",
        action="store_true",
        help="Delete existing --output-dir before sync.",
    )
    parser.add_argument(
        "--thumb-size",
        type=int,
        default=DEFAULT_THUMB_SIZE,
        help=f"Square thumbnail size in pixels for card/gallery previews (default: {DEFAULT_THUMB_SIZE}).",
    )
    parser.add_argument(
        "--max-image-edge",
        type=int,
        default=DEFAULT_MAX_IMAGE_EDGE,
        help=f"Resize every image so its longest edge is at most this many pixels (default: {DEFAULT_MAX_IMAGE_EDGE}).",
    )
    parser.add_argument(
        "--jpeg-quality",
        type=int,
        default=DEFAULT_JPEG_QUALITY,
        help=f"JPEG quality used for optimized images/thumbnails (default: {DEFAULT_JPEG_QUALITY}).",
    )
    parser.add_argument(
        "--thumbs-only",
        action="store_true",
        help="Use only thumbnail paths in kittens.json and remove full-size local images after thumbnail generation.",
    )
    return parser.parse_args()


def escape_query_value(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def list_children(service, parent_id: str, folders_only: bool = False) -> List[DriveFile]:
    query = f"'{parent_id}' in parents and trashed=false"
    if folders_only:
        query += f" and mimeType='{FOLDER_MIME}'"

    entries: List[DriveFile] = []
    page_token: Optional[str] = None

    while True:
        response = (
            service.files()
            .list(
                q=query,
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType)",
                pageSize=1000,
                orderBy="folder,name_natural",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token,
            )
            .execute()
        )
        for item in response.get("files", []):
            entries.append(
                DriveFile(
                    id=item["id"],
                    name=item["name"],
                    mime_type=item["mimeType"],
                )
            )
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    return entries


def find_folder_by_name(service, folder_name: str) -> str:
    query = (
        f"name='{escape_query_value(folder_name)}' and trashed=false "
        f"and mimeType='{FOLDER_MIME}'"
    )
    response = (
        service.files()
        .list(
            q=query,
            spaces="drive",
            fields="files(id, name)",
            pageSize=20,
            orderBy="name_natural",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        )
        .execute()
    )
    files = response.get("files", [])
    if not files:
        raise RuntimeError(f'Folder "{folder_name}" was not found in Google Drive.')
    if len(files) > 1:
        print(
            f'Warning: found {len(files)} folders named "{folder_name}". '
            f'Using the first one: {files[0]["id"]}',
            file=sys.stderr,
        )
    return files[0]["id"]


def build_drive_service(args: argparse.Namespace):
    if args.service_account_file:
        creds = service_account.Credentials.from_service_account_file(
            args.service_account_file, scopes=SCOPES
        )
        return build("drive", "v3", credentials=creds)

    credentials_path = Path(args.credentials_file)
    token_path = Path(args.token_file)

    if not credentials_path.exists():
        raise RuntimeError(
            f"Missing OAuth client file: {credentials_path}\n"
            "Create Desktop OAuth credentials in Google Cloud and save JSON there."
        )

    creds: Optional[Credentials] = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            try:
                creds = flow.run_local_server(port=0)
            except Exception:
                creds = flow.run_console()
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("drive", "v3", credentials=creds)


def sanitize_segment(name: str) -> str:
    cleaned = INVALID_FILE_CHARS.sub("_", name.strip())
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)
    return cleaned.strip("_") or "untitled"


def file_is_image(drive_file: DriveFile) -> bool:
    suffix = Path(drive_file.name).suffix.lower()
    return suffix in IMAGE_EXTS or drive_file.mime_type.startswith("image/")


def file_is_video(drive_file: DriveFile) -> bool:
    suffix = Path(drive_file.name).suffix.lower()
    return suffix in VIDEO_EXTS or drive_file.mime_type.startswith("video/")


def download_file(service, file_id: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    with destination.open("wb") as handle:
        downloader = MediaIoBaseDownload(handle, request, chunksize=1024 * 1024)
        done = False
        while not done:
            _, done = downloader.next_chunk()


def find_existing_local_file(base_dir: Path, local_file_name: str, is_image: bool) -> Optional[Path]:
    """Return an existing local file path for this Drive file if present."""
    primary = base_dir / local_file_name
    if primary.exists():
        return primary

    if not is_image:
        return None

    source_path = Path(local_file_name)
    suffix = source_path.suffix.lower()
    if suffix == ".jpg":
        return None

    # Common optimized output path (<stem>.jpg).
    optimized_jpg = base_dir / f"{source_path.stem}.jpg"
    if optimized_jpg.exists():
        return optimized_jpg

    # Alternate names used when collisions happened during prior optimization.
    ext_slug = source_path.suffix.lstrip(".").lower()
    if ext_slug:
        alt = base_dir / f"{source_path.stem}_{ext_slug}.jpg"
        if alt.exists():
            return alt

        prefixed = sorted(base_dir.glob(f"{source_path.stem}_{ext_slug}_*.jpg"))
        if prefixed:
            return prefixed[0]

    return None


def _resampling_lanczos():
    try:
        return Image.Resampling.LANCZOS  # Pillow >= 9
    except AttributeError:
        return Image.LANCZOS


def create_square_thumbnail(source: Path, destination: Path, size: int, jpeg_quality: int) -> None:
    with Image.open(source) as raw:
        image = ImageOps.exif_transpose(raw)

        if image.mode in ("RGBA", "LA"):
            base = Image.new("RGB", image.size, (255, 255, 255))
            alpha = image.getchannel("A")
            base.paste(image.convert("RGB"), mask=alpha)
            image = base
        elif image.mode != "RGB":
            image = image.convert("RGB")

        thumb = ImageOps.fit(
            image,
            (size, size),
            method=_resampling_lanczos(),
            centering=(0.5, 0.5),
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    thumb.save(
        destination,
        format="JPEG",
        quality=jpeg_quality,
        optimize=True,
        progressive=True,
        subsampling=0,
    )


def optimize_image_for_web(path: Path, max_image_edge: int, jpeg_quality: int) -> Path:
    def pick_output_path(input_path: Path) -> Path:
        base = input_path.with_suffix(".jpg")
        if base == input_path or not base.exists():
            return base

        alt = input_path.with_name(f"{input_path.stem}_{input_path.suffix.lstrip('.').lower()}.jpg")
        if not alt.exists():
            return alt

        counter = 2
        while True:
            candidate = input_path.with_name(
                f"{input_path.stem}_{input_path.suffix.lstrip('.').lower()}_{counter}.jpg"
            )
            if not candidate.exists():
                return candidate
            counter += 1

    with Image.open(path) as raw:
        image = ImageOps.exif_transpose(raw)
        width, height = image.size
        longest_edge = max(width, height)
        if max_image_edge > 0 and longest_edge > max_image_edge:
            scale = max_image_edge / float(longest_edge)
            new_size = (
                max(1, int(round(width * scale))),
                max(1, int(round(height * scale))),
            )
            image = image.resize(new_size, _resampling_lanczos())

        if image.mode in ("RGBA", "LA"):
            base = Image.new("RGB", image.size, (255, 255, 255))
            alpha = image.getchannel("A")
            base.paste(image.convert("RGB"), mask=alpha)
            image = base
        elif image.mode != "RGB":
            image = image.convert("RGB")

        # Save as JPEG in place (or convert extension) to keep files lightweight for git/web.
        jpeg_path = pick_output_path(path)
        image.save(
            jpeg_path,
            format="JPEG",
            quality=jpeg_quality,
            optimize=True,
            progressive=True,
            subsampling=0,
        )

    if jpeg_path != path and path.exists():
        path.unlink()
    return jpeg_path


def ensure_unique_file_name(file_name: str, used_names: Set[str], suffix_seed: str) -> str:
    if file_name not in used_names:
        used_names.add(file_name)
        return file_name

    candidate_path = Path(file_name)
    stem = candidate_path.stem
    ext = candidate_path.suffix
    candidate = f"{stem}_{suffix_seed}{ext}"
    counter = 2
    while candidate in used_names:
        candidate = f"{stem}_{suffix_seed}_{counter}{ext}"
        counter += 1
    used_names.add(candidate)
    return candidate


def extract_date(text: str) -> str:
    if not text:
        return ""
    match = DATE_PATTERN.search(text)
    return match.group(0) if match else ""


def parse_litter_name(folder_name: str) -> Tuple[str, str]:
    match = re.match(r"^(.*?)(?:\((.*?)\))?\s*$", folder_name.strip())
    if not match:
        raw = folder_name.strip()
        return raw, extract_date(raw)

    head = (match.group(1) or "").strip()
    date_part = (match.group(2) or "").strip()
    if "_" in head:
        prefix, rest = head.split("_", 1)
        prefix_fold = prefix.casefold()
        if prefix_fold.startswith("\u043f\u043e\u043c") or prefix_fold == "litter":
            head = rest.strip()

    litter_date = extract_date(date_part) or extract_date(head) or extract_date(folder_name)
    if litter_date:
        head = re.sub(rf"[\s_/-]*{re.escape(litter_date)}\s*$", "", head).strip(" _-")

    return head or folder_name.strip(), litter_date


def parse_kitten_folder(folder_name: str) -> Tuple[str, str, str]:
    match = re.match(r"^\s*([fFmM])\s*([^()]+?)\s*(?:\((.*?)\))?\s*$", folder_name)
    if match:
        gender_code = match.group(1).lower()
        gender = "female" if gender_code == "f" else "male"
        kitten_name = match.group(2).strip()
        details = (match.group(3) or "").strip()
        return kitten_name, gender, details

    fallback = re.match(r"^\s*([^()]+?)\s*(?:\((.*?)\))?\s*$", folder_name)
    if fallback:
        kitten_name = fallback.group(1).strip()
        details = (fallback.group(2) or "").strip()
        return kitten_name, "", details

    return folder_name.strip(), "", ""


def build_full_description(gender: str, details: str, litter_label: str, litter_date: str) -> str:
    lines: List[str] = []
    if gender:
        lines.append(f"Gender : {gender}")
    if details:
        lines.append(f"Details : {details}")
    if litter_date:
        lines.append(f"Date of birth : {litter_date}")
    return "\n".join(lines).strip() + ("\n" if lines else "")


def ensure_unique(value: str, used: Set[str], fallback_context: str) -> str:
    candidate = value
    if candidate and candidate not in used:
        used.add(candidate)
        return candidate

    if fallback_context:
        candidate = f"{value} ({fallback_context})" if value else fallback_context
        if candidate not in used:
            used.add(candidate)
            return candidate

    counter = 2
    while True:
        candidate = f"{value} {counter}".strip()
        if candidate not in used:
            used.add(candidate)
            return candidate
        counter += 1


def to_web_path(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    args = parse_args()
    if args.max_image_edge < 1:
        raise RuntimeError("--max-image-edge must be a positive integer.")
    if args.thumb_size < 1:
        raise RuntimeError("--thumb-size must be a positive integer.")
    if args.jpeg_quality < 1 or args.jpeg_quality > 95:
        raise RuntimeError("--jpeg-quality must be between 1 and 95.")

    project_root = Path.cwd()
    output_dir = Path(args.output_dir)
    json_output = Path(args.json_output)

    if args.wipe_output and output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    service = build_drive_service(args)
    root_folder_id = args.root_folder_id or find_folder_by_name(service, args.root_folder_name)
    skip_names = {name.casefold() for name in args.skip_folder}

    litter_folders = [
        folder
        for folder in list_children(service, root_folder_id, folders_only=True)
        if folder.mime_type == FOLDER_MIME
    ]

    kittens_payload: List[Dict[str, object]] = []
    used_kitten_names: Set[str] = set()
    used_local_dirs: Set[str] = set()
    downloaded_files = 0
    reused_files = 0

    for litter_folder in litter_folders:
        litter_label, litter_date = parse_litter_name(litter_folder.name)
        kitten_folders = [
            child
            for child in list_children(service, litter_folder.id, folders_only=True)
            if child.mime_type == FOLDER_MIME and child.name.casefold() not in skip_names
        ]

        for kitten_folder in kitten_folders:
            base_name, gender, details = parse_kitten_folder(kitten_folder.name)
            kitten_name = ensure_unique(base_name, used_kitten_names, litter_label)

            local_dir_name = sanitize_segment(base_name)
            if not local_dir_name:
                local_dir_name = sanitize_segment(kitten_name)
            local_dir_name = ensure_unique(local_dir_name, used_local_dirs, sanitize_segment(litter_label))
            kitten_dir = output_dir / local_dir_name
            kitten_dir.mkdir(parents=True, exist_ok=True)

            full_text = build_full_description(gender, details, litter_label, litter_date)
            (kitten_dir / "desc.txt").write_text((gender + "\n") if gender else "", encoding="utf-8")
            (kitten_dir / "full_description.txt").write_text(full_text, encoding="utf-8")

            child_files = [
                child
                for child in list_children(service, kitten_folder.id, folders_only=False)
                if child.mime_type != FOLDER_MIME
            ]

            image_local_paths: List[Path] = []
            image_paths: List[str] = []
            video_paths: List[str] = []
            used_file_names: Set[str] = set()

            print(f"Syncing kitten: {kitten_name} (files: {len(child_files)})")
            for drive_file in child_files:
                is_image = file_is_image(drive_file)
                is_video = file_is_video(drive_file)
                if not is_image and not is_video:
                    continue
                if is_video and args.skip_videos:
                    continue

                local_file_name = sanitize_segment(drive_file.name)
                local_file_name = ensure_unique_file_name(
                    local_file_name, used_file_names, drive_file.id[:8]
                )
                local_file = kitten_dir / local_file_name
                existing_local = find_existing_local_file(
                    kitten_dir,
                    local_file_name,
                    is_image=is_image,
                )
                if existing_local:
                    local_file = existing_local
                    reused_files += 1
                    print(f"  Reusing existing: {local_file.name}")
                else:
                    download_file(service, drive_file.id, local_file)
                    downloaded_files += 1
                if is_image:
                    if not existing_local:
                        try:
                            local_file = optimize_image_for_web(
                                local_file,
                                max_image_edge=args.max_image_edge,
                                jpeg_quality=args.jpeg_quality,
                            )
                        except Exception as exc:
                            print(
                                f"Warning: could not optimize image '{local_file.name}': {exc}",
                                file=sys.stderr,
                            )
                    image_local_paths.append(local_file)
                    image_paths.append(to_web_path(local_file, project_root))
                elif is_video:
                    video_paths.append(to_web_path(local_file, project_root))

            if not image_paths:
                print(
                    f"Skipping kitten '{kitten_name}' because no images were found.",
                    file=sys.stderr,
                )
                continue

            thumb_paths: List[str] = []
            thumb_generated_ok: List[bool] = []
            for image_local_path in image_local_paths:
                thumb_name = f"{image_local_path.stem}__thumb.jpg"
                thumb_local_path = kitten_dir / THUMB_DIR_NAME / thumb_name
                try:
                    create_square_thumbnail(
                        image_local_path,
                        thumb_local_path,
                        args.thumb_size,
                        args.jpeg_quality,
                    )
                    thumb_paths.append(to_web_path(thumb_local_path, project_root))
                    thumb_generated_ok.append(True)
                except Exception as exc:
                    print(
                        f"Warning: could not generate thumbnail for '{image_local_path.name}': {exc}",
                        file=sys.stderr,
                    )
                    thumb_paths.append(to_web_path(image_local_path, project_root))
                    thumb_generated_ok.append(False)

            if args.thumbs_only and thumb_paths:
                for index, image_local_path in enumerate(image_local_paths):
                    if index < len(thumb_generated_ok) and thumb_generated_ok[index] and image_local_path.exists():
                        image_local_path.unlink()
                display_paths = thumb_paths
            else:
                display_paths = image_paths

            kittens_payload.append(
                {
                    "name": kitten_name,
                    "desc": gender,
                    "txt": full_text,
                    "image": display_paths[0],
                    "thumbnail": thumb_paths[0] if thumb_paths else display_paths[0],
                    "images": display_paths,
                    "thumbs": thumb_paths if thumb_paths else display_paths,
                    "videos": video_paths,
                }
            )

    json_output.write_text(
        json.dumps(kittens_payload, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )

    print(
        f"Done. Synced {len(kittens_payload)} kittens.\n"
        f"Downloaded files: {downloaded_files}\n"
        f"Reused existing files: {reused_files}\n"
        f"Media directory: {output_dir}\n"
        f"JSON file: {json_output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
