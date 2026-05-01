"""
剪映草稿路径修复工具
- 将 draft_content.json 中的相对路径转换为绝对路径
- 生成 fix_paths.bat 修复脚本（兜底方案）
"""

import copy
import json
import os


def apply_extract_path(draft_json: dict, extract_path: str, draft_name: str) -> dict:
    """将 draft_content.json 中的相对路径转为基于 extract_path 的绝对路径。

    拼接规则: {extract_path}\\{draft_name}\\{relative_path}
    """
    data = copy.deepcopy(draft_json)
    base = os.path.join(extract_path, draft_name)

    for video in data.get("materials", {}).get("videos", []):
        if "path" in video and not os.path.isabs(video["path"]):
            video["path"] = os.path.join(base, video["path"]).replace("/", "\\")

    for audio in data.get("materials", {}).get("audios", []):
        if "path" in audio and not os.path.isabs(audio["path"]):
            audio["path"] = os.path.join(base, audio["path"]).replace("/", "\\")

    return data


def generate_fix_bat() -> str:
    """生成 fix_paths.bat 修复脚本。

    用户解压到非预期位置时，双击此脚本即可将 draft_content.json
    中的素材路径替换为当前文件夹的绝对路径。
    """
    return r'''@echo off
chcp 65001 >nul
echo ===================================
echo  剪映草稿路径修复工具
echo ===================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "JSON_FILE=%SCRIPT_DIR%\draft_content.json"

if not exist "%JSON_FILE%" (
    echo [错误] 未找到 draft_content.json，请确保此脚本与草稿文件在同一目录。
    pause
    exit /b 1
)

echo 当前目录: %SCRIPT_DIR%
echo 正在修复路径...

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$dir = '%SCRIPT_DIR%';" ^
    "$jsonPath = '%JSON_FILE%';" ^
    "$data = Get-Content $jsonPath -Raw -Encoding UTF8;" ^
    "$json = $data | ConvertFrom-Json;" ^
    "$changed = 0;" ^
    "foreach ($v in $json.materials.videos) {" ^
    "  if ($v.path -and -not [System.IO.Path]::IsPathRooted($v.path)) {" ^
    "    $v.path = [System.IO.Path]::Combine($dir, $v.path).Replace('/', '\');" ^
    "    $changed++;" ^
    "  }" ^
    "}" ^
    "foreach ($a in $json.materials.audios) {" ^
    "  if ($a.path -and -not [System.IO.Path]::IsPathRooted($a.path)) {" ^
    "    $a.path = [System.IO.Path]::Combine($dir, $a.path).Replace('/', '\');" ^
    "    $changed++;" ^
    "  }" ^
    "}" ^
    "$json | ConvertTo-Json -Depth 100 | Set-Content $jsonPath -Encoding UTF8;" ^
    "Write-Host \"已修复 $changed 个路径\";"

echo.
echo 修复完成！现在可以在剪映中打开此草稿。
pause
'''
