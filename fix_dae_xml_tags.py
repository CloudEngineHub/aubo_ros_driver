import argparse
import os
import re


SELF_CLOSING_TAGS = ["author", "comments", "keywords", "revision", "subject", "title"]


def replace_tags_in_dae_files(directory, write_changes=False):
    dae_count = 0
    modified_count = 0
    pending_count = 0
    skipped_count = 0

    # 获取目录中的所有 DAE 文件
    for root, _, files in os.walk(directory):
        for file_name in files:
            if not file_name.lower().endswith(".dae"):
                continue

            dae_count += 1
            file_path = os.path.join(root, file_name)

            # 跳过软链接，避免误修改链接指向的真实文件
            if os.path.islink(file_path):
                skipped_count += 1
                print(
                    "Skipped symlink: {} -> {}".format(
                        file_path, os.path.realpath(file_path)
                    )
                )
                continue

            # 跳过无法访问的文件，避免单个异常中断整个批处理
            try:
                with open(file_path, "r", encoding="utf-8") as file:
                    original_content = file.read()
            except OSError as exc:
                skipped_count += 1
                print("Skipped file: {} ({})".format(file_path, exc))
                continue

            content = original_content

            # 将自闭合标签替换为完整标签，兼容部分 ROS1 XML 解析场景
            for tag in SELF_CLOSING_TAGS:
                pattern = r"<{}/>".format(tag)
                replace = "<{}></{}>".format(tag, tag)
                content = re.sub(pattern, replace, content)

            # 默认仅预览将要修改的文件，显式开启写入时才落盘
            if content != original_content:
                pending_count += 1
                if not write_changes:
                    print("Would modify file:", file_path)
                    continue

                try:
                    with open(file_path, "w", encoding="utf-8") as file:
                        file.write(content)
                except OSError as exc:
                    skipped_count += 1
                    print("Skipped file: {} ({})".format(file_path, exc))
                    continue
                modified_count += 1
                print("Modified file:", file_path)

    if write_changes:
        print(
            "Scanned {} DAE files, modified {} files, skipped {} files.".format(
                dae_count, modified_count, skipped_count
            )
        )
    else:
        print(
            "Scanned {} DAE files, {} files would be modified, skipped {} files.".format(
                dae_count, pending_count, skipped_count
            )
        )


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_directory = os.path.join(script_dir, "aubo_description", "meshes")

    parser = argparse.ArgumentParser(
        description="Fix self-closing XML tags in DAE files for ROS1 compatibility."
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default=default_directory,
        help="Directory to scan recursively. Default: %(default)s",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Actually write changes to DAE files. Without this flag, the script only previews changes.",
    )
    args = parser.parse_args()

    target_directory = os.path.abspath(args.directory)
    if not os.path.isdir(target_directory):
        parser.exit(
            1, "Error: directory not found: {}\n".format(target_directory)
        )

    replace_tags_in_dae_files(target_directory, write_changes=args.write)


if __name__ == "__main__":
    main()
