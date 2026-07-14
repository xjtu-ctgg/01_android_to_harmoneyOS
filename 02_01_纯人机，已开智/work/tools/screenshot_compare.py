#!/usr/bin/env python3
"""Compare two raw PNG screenshots without third-party Python packages."""

from __future__ import annotations

import argparse
import json
import math
import struct
import sys
import zlib
from pathlib import Path


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


class PngInputError(ValueError):
    """Raised when a PNG is unsupported or malformed."""


def paeth(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    left_distance = abs(estimate - left)
    above_distance = abs(estimate - above)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def unfilter_row(filter_type: int, encoded: bytes, previous: bytes, bytes_per_pixel: int) -> bytes:
    decoded = bytearray(len(encoded))
    for index, value in enumerate(encoded):
        left = decoded[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
        above = previous[index] if previous else 0
        upper_left = previous[index - bytes_per_pixel] if previous and index >= bytes_per_pixel else 0
        if filter_type == 0:
            prediction = 0
        elif filter_type == 1:
            prediction = left
        elif filter_type == 2:
            prediction = above
        elif filter_type == 3:
            prediction = (left + above) // 2
        elif filter_type == 4:
            prediction = paeth(left, above, upper_left)
        else:
            raise PngInputError("unsupported_png_filter")
        decoded[index] = (value + prediction) & 0xFF
    return bytes(decoded)


def composite_channel(channel: int, alpha: int) -> int:
    return (channel * alpha + 255 * (255 - alpha) + 127) // 255


def row_to_rgb(row: bytes, color_type: int) -> list[tuple[int, int, int]]:
    pixels: list[tuple[int, int, int]] = []
    if color_type == 0:
        pixels.extend((value, value, value) for value in row)
    elif color_type == 2:
        pixels.extend((row[index], row[index + 1], row[index + 2]) for index in range(0, len(row), 3))
    elif color_type == 4:
        for index in range(0, len(row), 2):
            gray = row[index]
            alpha = row[index + 1]
            value = composite_channel(gray, alpha)
            pixels.append((value, value, value))
    elif color_type == 6:
        for index in range(0, len(row), 4):
            alpha = row[index + 3]
            pixels.append(
                (
                    composite_channel(row[index], alpha),
                    composite_channel(row[index + 1], alpha),
                    composite_channel(row[index + 2], alpha),
                )
            )
    return pixels


def read_png(path: Path) -> tuple[int, int, list[tuple[int, int, int]]]:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise PngInputError("invalid_png_signature")
    offset = len(PNG_SIGNATURE)
    width = 0
    height = 0
    bit_depth = -1
    color_type = -1
    interlace = -1
    compressed = bytearray()
    saw_end = False
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        crc_end = payload_end + 4
        if crc_end > len(data):
            raise PngInputError("truncated_png_chunk")
        payload = data[payload_start:payload_end]
        expected_crc = struct.unpack(">I", data[payload_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type)
        actual_crc = zlib.crc32(payload, actual_crc) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise PngInputError("png_crc_mismatch")
        if chunk_type == b"IHDR":
            if length != 13:
                raise PngInputError("invalid_ihdr")
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(
                ">IIBBBBB", payload
            )
            if compression != 0 or filter_method != 0:
                raise PngInputError("unsupported_png_encoding")
        elif chunk_type == b"IDAT":
            compressed.extend(payload)
        elif chunk_type == b"IEND":
            saw_end = True
            break
        offset = crc_end
    if width <= 0 or height <= 0 or not compressed or not saw_end:
        raise PngInputError("incomplete_png")
    if bit_depth != 8 or color_type not in (0, 2, 4, 6) or interlace != 0:
        raise PngInputError("unsupported_png_format")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}[color_type]
    row_length = width * channels
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error as error:
        raise PngInputError("invalid_png_compression") from error
    expected_length = height * (row_length + 1)
    if len(raw) != expected_length:
        raise PngInputError("unexpected_png_data_length")
    pixels: list[tuple[int, int, int]] = []
    previous = b""
    for row_index in range(height):
        start = row_index * (row_length + 1)
        filter_type = raw[start]
        encoded = raw[start + 1:start + 1 + row_length]
        decoded = unfilter_row(filter_type, encoded, previous, channels)
        pixels.extend(row_to_rgb(decoded, color_type))
        previous = decoded
    return width, height, pixels


def luminance(pixel: tuple[int, int, int]) -> float:
    return (77 * pixel[0] + 150 * pixel[1] + 29 * pixel[2]) / 256


def window_ssim(reference: list[float], actual: list[float]) -> float:
    count = len(reference)
    reference_mean = sum(reference) / count
    actual_mean = sum(actual) / count
    reference_variance = sum((value - reference_mean) ** 2 for value in reference) / count
    actual_variance = sum((value - actual_mean) ** 2 for value in actual) / count
    covariance = sum(
        (reference[index] - reference_mean) * (actual[index] - actual_mean) for index in range(count)
    ) / count
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2
    numerator = (2 * reference_mean * actual_mean + c1) * (2 * covariance + c2)
    denominator = (reference_mean ** 2 + actual_mean ** 2 + c1) * (
        reference_variance + actual_variance + c2
    )
    return numerator / denominator if denominator else 1


def calculate_ssim(
    reference: list[tuple[int, int, int]], actual: list[tuple[int, int, int]], width: int, height: int
) -> float:
    window_size = 8
    scores: list[float] = []
    for top in range(0, height, window_size):
        for left in range(0, width, window_size):
            reference_window: list[float] = []
            actual_window: list[float] = []
            for y in range(top, min(top + window_size, height)):
                row_offset = y * width
                for x in range(left, min(left + window_size, width)):
                    index = row_offset + x
                    reference_window.append(luminance(reference[index]))
                    actual_window.append(luminance(actual[index]))
            scores.append(window_ssim(reference_window, actual_window))
    return sum(scores) / len(scores)


def calculate_metrics(
    reference: list[tuple[int, int, int]],
    actual: list[tuple[int, int, int]],
    width: int,
    height: int,
    pixel_threshold: int,
) -> dict[str, float]:
    absolute_error = 0
    mismatched_pixels = 0
    for reference_pixel, actual_pixel in zip(reference, actual):
        channel_errors = [abs(reference_pixel[index] - actual_pixel[index]) for index in range(3)]
        absolute_error += sum(channel_errors)
        if max(channel_errors) > pixel_threshold:
            mismatched_pixels += 1
    pixel_count = len(reference)
    return {
        "meanAbsoluteError": round(absolute_error / (pixel_count * 3), 6),
        "pixelMismatchRate": round(mismatched_pixels / pixel_count, 6),
        "ssim": round(calculate_ssim(reference, actual, width, height), 6),
    }


def write_report(output: Path, payload: dict[str, object]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True, help="Raw Android reference PNG")
    parser.add_argument("--actual", type=Path, required=True, help="Raw HarmonyOS PNG")
    parser.add_argument("--output", type=Path, required=True, help="JSON report path")
    parser.add_argument("--max-mae", type=float, default=12)
    parser.add_argument("--max-mismatch-rate", type=float, default=0.1)
    parser.add_argument("--min-ssim", type=float, default=0.95)
    parser.add_argument("--pixel-threshold", type=int, default=16)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not math.isfinite(args.max_mae) or args.max_mae < 0:
        return 2
    if not 0 <= args.max_mismatch_rate <= 1 or not 0 <= args.min_ssim <= 1:
        return 2
    if not 0 <= args.pixel_threshold <= 255:
        return 2
    try:
        reference_width, reference_height, reference_pixels = read_png(args.reference)
        actual_width, actual_height, actual_pixels = read_png(args.actual)
    except (OSError, PngInputError) as error:
        payload: dict[str, object] = {
            "status": "input_error",
            "reason": str(error),
            "reference": args.reference.name,
            "actual": args.actual.name,
        }
        write_report(args.output, payload)
        return 2
    if (reference_width, reference_height) != (actual_width, actual_height):
        write_report(
            args.output,
            {
                "status": "input_error",
                "reason": "dimension_mismatch",
                "reference": args.reference.name,
                "actual": args.actual.name,
                "referenceSize": {"width": reference_width, "height": reference_height},
                "actualSize": {"width": actual_width, "height": actual_height},
            },
        )
        return 2
    metrics = calculate_metrics(
        reference_pixels,
        actual_pixels,
        reference_width,
        reference_height,
        args.pixel_threshold,
    )
    failed_thresholds: list[str] = []
    if metrics["meanAbsoluteError"] > args.max_mae:
        failed_thresholds.append("mean_absolute_error")
    if metrics["pixelMismatchRate"] > args.max_mismatch_rate:
        failed_thresholds.append("pixel_mismatch_rate")
    if metrics["ssim"] < args.min_ssim:
        failed_thresholds.append("ssim")
    write_report(
        args.output,
        {
            "status": "failed" if failed_thresholds else "passed",
            "reference": args.reference.name,
            "actual": args.actual.name,
            "size": {"width": reference_width, "height": reference_height},
            "thresholds": {
                "maxMeanAbsoluteError": args.max_mae,
                "maxPixelMismatchRate": args.max_mismatch_rate,
                "minSsim": args.min_ssim,
                "pixelThreshold": args.pixel_threshold,
            },
            "metrics": metrics,
            "failedThresholds": failed_thresholds,
        },
    )
    return 1 if failed_thresholds else 0


if __name__ == "__main__":
    sys.exit(main())
