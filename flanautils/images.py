import pathlib
from collections.abc import Iterable, Sequence
from enum import Enum, auto

import cv2
import mss
import mss.screenshot
import numpy


class SortBy(Enum):
    CONFIDENCE = auto()
    Y = auto()
    X = auto()


def _get_base_image(
    sub_image: str | pathlib.Path | numpy.ndarray,
    image: str | pathlib.Path | numpy.ndarray
) -> numpy.ndarray:
    sub_image = to_ndarray(sub_image)
    image = to_ndarray(image)

    width = max(sub_image.shape[1], image.shape[1])
    height = max(sub_image.shape[0], image.shape[0])
    image_ = numpy.zeros((height, width, 3), dtype=numpy.uint8)
    image_[0:image.shape[0], 0:image.shape[1]] = image

    return image_


def _swap_axis_in_place(array: numpy.ndarray):
    array[:, 0], array[:, 1] = array[:, 1], array[:, 0].copy()


def compare(
    a: str | pathlib.Path | numpy.ndarray,
    b: str | pathlib.Path | numpy.ndarray,
    mask: str | pathlib.Path | numpy.ndarray = None
) -> float:
    _, score, _, _ = cv2.minMaxLoc(match(a, b, mask))
    return score


def get_all_positions_in_image(
    sub_images: str | pathlib.Path | numpy.ndarray | Iterable[str | pathlib.Path | numpy.ndarray],
    image: str | pathlib.Path | numpy.ndarray,
    mask: str | pathlib.Path | numpy.ndarray = None,
    confidence=1.0,
    center=False,
    sort_by: SortBy | Iterable[SortBy] = None
) -> numpy.ndarray:
    def add_confidence(array: numpy.ndarray) -> numpy.ndarray:
        return numpy.array([*array, 1 - matches[*array]])

    def center_points(array: numpy.ndarray) -> numpy.ndarray:
        # noinspection PyTypeChecker
        return numpy.array([*get_center(array[0], array[1], sub_image.shape[0], sub_image.shape[1]), array[2]])

    def process_sort_by(sort_by_):
        match sort_by_:
            case None:
                new_sort_by = list(SortBy)
            case [*_]:
                new_sort_by = []
                for category in sort_by_:
                    if category not in new_sort_by:
                        new_sort_by.append(category)
            case _:
                new_sort_by = [sort_by_]
        for category in iter(SortBy):
            if category not in new_sort_by:
                new_sort_by.append(category)
        return new_sort_by

    if isinstance(sub_images, str | pathlib.Path | numpy.ndarray):
        sub_images = (sub_images,)
    sort_by = process_sort_by(sort_by)

    all_points = numpy.empty((0, 3), dtype=float)
    for sub_image in sub_images:
        sub_image = to_ndarray(sub_image)
        matches = match(sub_image, image, mask)
        points = numpy.argwhere(matches >= confidence)
        if not points.size:
            continue
        points = numpy.apply_along_axis(add_confidence, 1, points)
        if center:
            points = numpy.apply_along_axis(center_points, 1, points)
        all_points = numpy.concatenate((all_points, points))

    _swap_axis_in_place(all_points)
    all_points = numpy.core.records.fromarrays(all_points.transpose(), names='x, y, confidence', formats='int, int, float')

    if sort_by != [SortBy.Y, SortBy.X, SortBy.CONFIDENCE]:
        all_points.sort(order=[category.name.lower() for category in sort_by])

    # restore confidence value for reverse sort
    if all_points.size:
        all_points['confidence'] = 1 - all_points['confidence']

    return all_points


def get_all_positions_in_screen(
    sub_images: str | pathlib.Path | numpy.ndarray | Iterable[str | pathlib.Path | numpy.ndarray],
    mask: str | pathlib.Path | numpy.ndarray = None,
    region: Sequence[int, int, int, int] = None,
    confidence=1.0,
    center=False,
    region_relative_coordinates=False,
    sort_by: SortBy | Iterable[SortBy] = None
) -> tuple[numpy.ndarray, numpy.ndarray]:
    image, (left, top) = get_screenshot(region)
    points = get_all_positions_in_image(sub_images, image, mask, confidence, center, sort_by)

    if points.size and not region_relative_coordinates:
        points['x'] += left
        points['y'] += top

    return points, image


def get_center(x: int, y: int, width: int, height: int) -> tuple[int, int]:
    return x + round(width / 2), y + round(height / 2)


def get_screenshot(
    region: Sequence[int, int, int, int] = None,
    capturer: mss.base.MSSBase = None
) -> tuple[numpy.ndarray, tuple[int, int]]:
    def get_mss_region(region_: Sequence[int, int, int, int] = None) -> dict[str, int]:
        if region_:
            return {
                "left": region_[0],
                "top": region_[1],
                "width": region_[2] - region_[0],
                "height": region_[3] - region_[1],
            }
        else:
            return capturer.monitors[0]

    if capturer:
        region = get_mss_region(region)
        screenshot = capturer.grab(region)
    else:
        with mss.mss() as capturer:
            region = get_mss_region(region)
            screenshot = capturer.grab(region)

    return to_ndarray(screenshot), (region['left'], region['top'])


def is_region_color(
    region: Sequence[int, int, int, int],
    target_color: tuple[int, int, int],
    tolerance: int
) -> bool:
    color = region_color_mean(region)
    return (
        abs(target_color[0] - color[0]) < tolerance
        and
        abs(target_color[1] - color[1]) < tolerance
        and
        abs(target_color[2] - color[2]) < tolerance
    )


def match(
    sub_image: str | pathlib.Path | numpy.ndarray,
    image: str | pathlib.Path | numpy.ndarray,
    mask: str | pathlib.Path | numpy.ndarray = None,
) -> numpy.ndarray:
    sub_image = to_ndarray(sub_image)
    image = _get_base_image(sub_image, image)

    kwargs = {}
    if mask:
        kwargs['mask'] = to_ndarray(mask)

    return cv2.matchTemplate(image, sub_image, cv2.TM_CCOEFF_NORMED, **kwargs)


def region_color_mean(region: Sequence[int, int, int, int]) -> tuple[int, int, int]:
    image, _ = get_screenshot(region)
    image = image.astype(numpy.uint16)

    red_sum = (image ** 2)[:, :, 0].sum(dtype=numpy.uint64)
    green_sum = (image ** 2)[:, :, 1].sum(dtype=numpy.uint64)
    blue_sum = (image ** 2)[:, :, 2].sum(dtype=numpy.uint64)

    n_pixels = image.shape[0] * image.shape[1]

    return (
        round((red_sum / n_pixels) ** (1 / 2)),
        round((green_sum / n_pixels) ** (1 / 2)),
        round((blue_sum / n_pixels) ** (1 / 2))
    )


def search_in_image(
    sub_image: str | pathlib.Path | numpy.ndarray,
    image: str | pathlib.Path | numpy.ndarray,
    mask: str | pathlib.Path | numpy.ndarray = None,
    confidence=1.0,
    center=False
) -> tuple[int, int] | None:
    sub_image = to_ndarray(sub_image)
    matches = match(sub_image, image, mask)
    _, confidence_, _, (x, y) = cv2.minMaxLoc(matches)
    if confidence_ < confidence:
        return

    if center:
        x, y = get_center(x, y, sub_image.shape[1], sub_image.shape[0])

    return x, y


def search_in_screen(
    sub_image: str | pathlib.Path | numpy.ndarray,
    mask: str | pathlib.Path | numpy.ndarray = None,
    region: Sequence[int, int, int, int] = None,
    confidence=1.0,
    center=False,
    region_relative_coordinates=False
) -> tuple[tuple[int, int], numpy.ndarray] | None:
    image, (left, top) = get_screenshot(region)
    if not (point := search_in_image(
        sub_image,
        image,
        mask,
        confidence,
        center
    )):
        return

    if not region_relative_coordinates:
        point = (point[0] + left, point[1] + top)

    return point, image


def to_ndarray(image: str | pathlib.Path | mss.screenshot.ScreenShot | numpy.ndarray) -> numpy.ndarray:
    match image:
        case str() | pathlib.Path():
            image = cv2.imread(str(image))
        case mss.screenshot.ScreenShot():
            image = numpy.array(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return image[:, :, :3]
