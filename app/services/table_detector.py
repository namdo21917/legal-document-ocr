import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.utils.exceptions import ImageError
from app.utils.logger import Logger


class TableDetector:
    def __init__(self, config):
        """
        Khởi tạo TableDetector
        Args:
            config: Dict cấu hình cho việc nhận diện bảng
        """
        self.logger = Logger(__name__).logger
        self.config = config['table_detection']
        self.logger.debug("Khởi tạo TableDetector với cấu hình: " + str(self.config))

    def _detect_lines(self, image):
        """
        Phát hiện các đường kẻ ngang và dọc trong ảnh
        Args:
            image: Ảnh đầu vào (grayscale)
        Returns:
            tuple: (đường ngang, đường dọc)
        """
        try:
            # Áp dụng threshold
            _, threshold = cv2.threshold(image,
                                         self.config['threshold_value'],
                                         255,
                                         cv2.THRESH_BINARY_INV)

            # Phát hiện đường kẻ ngang
            horizontal_kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (self.config['horizontal_kernel_length'], 1)
            )
            horizontal_lines = cv2.morphologyEx(
                threshold,
                cv2.MORPH_OPEN,
                horizontal_kernel,
                iterations=self.config['line_detection_iterations']
            )

            # Phát hiện đường kẻ dọc
            vertical_kernel = cv2.getStructuringElement(
                cv2.MORPH_RECT,
                (1, self.config['vertical_kernel_length'])
            )
            vertical_lines = cv2.morphologyEx(
                threshold,
                cv2.MORPH_OPEN,
                vertical_kernel,
                iterations=self.config['line_detection_iterations']
            )

            return horizontal_lines, vertical_lines

        except Exception as e:
            self.logger.error(f"Lỗi phát hiện đường kẻ: {str(e)}")
            raise ImageError("Lỗi phát hiện đường kẻ trong bảng")

    def _find_intersections(self, h_lines, v_lines):
        """
        Tìm các điểm giao nhau giữa đường ngang và dọc
        Args:
            h_lines: Ảnh chứa đường kẻ ngang
            v_lines: Ảnh chứa đường kẻ dọc
        Returns:
            list: Danh sách các điểm giao nhau
        """
        try:
            # Kết hợp đường ngang và dọc
            joints = cv2.bitwise_and(h_lines, v_lines)

            # Tìm tọa độ các điểm giao nhau
            coords = np.column_stack(np.where(joints > 0))

            # Gom nhóm các điểm gần nhau
            intersections = []
            for coord in coords:
                added = False
                for i, point in enumerate(intersections):
                    if np.linalg.norm(coord - point) < self.config['intersection_threshold']:
                        intersections[i] = (intersections[i] + coord) / 2
                        added = True
                        break
                if not added:
                    intersections.append(coord)

            return np.array(intersections)

        except Exception as e:
            self.logger.error(f"Lỗi tìm điểm giao: {str(e)}")
            raise ImageError("Lỗi tìm điểm giao trong bảng")

    def _extract_cells(self, image, intersections):
        """
        Trích xuất các ô trong bảng
        Args:
            image: Ảnh gốc
            intersections: Các điểm giao nhau
        Returns:
            list: Danh sách các ô trong bảng
        """
        try:
            # Sắp xếp các điểm theo hàng và cột
            sorted_points = intersections[np.lexsort((intersections[:, 1], intersections[:, 0]))]

            cells = []
            for i in range(len(sorted_points) - 1):
                for j in range(len(sorted_points) - 1):
                    top_left = sorted_points[i]
                    bottom_right = sorted_points[i + 1]

                    # Trích xuất vùng ảnh của ô
                    cell = image[
                           int(top_left[0]):int(bottom_right[0]),
                           int(top_left[1]):int(bottom_right[1])
                           ]

                    if cell.size > 0:  # Kiểm tra ô không rỗng
                        cells.append({
                            'image': cell,
                            'position': (i, j),
                            'bbox': (
                                int(top_left[1]), int(top_left[0]),
                                int(bottom_right[1]), int(bottom_right[0])
                            )
                        })

            return cells

        except Exception as e:
            self.logger.error(f"Lỗi trích xuất ô: {str(e)}")
            raise ImageError("Lỗi trích xuất ô trong bảng")

    def detect_tables(self, image):
        """
        Phát hiện và trích xuất các bảng trong ảnh
        Args:
            image: Ảnh đầu vào (PIL Image hoặc numpy array)
        Returns:
            list: Danh sách các bảng phát hiện được
        """
        self.logger.info("Bắt đầu phát hiện bảng")
        try:
            # Chuyển đổi ảnh sang grayscale nếu cần
            if isinstance(image, Image.Image):
                image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Phát hiện đường kẻ
            h_lines, v_lines = self._detect_lines(gray)

            # Tìm các điểm giao nhau
            intersections = self._find_intersections(h_lines, v_lines)

            if len(intersections) < 4:  # Cần ít nhất 4 điểm để tạo thành bảng
                self.logger.warning("Không phát hiện được bảng")
                return []

            # Trích xuất các ô trong bảng
            cells = self._extract_cells(gray, intersections)

            # Tạo thông tin về bảng
            table_info = {
                'cells': cells,
                'num_rows': len(set(cell['position'][0] for cell in cells)),
                'num_cols': len(set(cell['position'][1] for cell in cells)),
                'intersections': intersections.tolist()
            }

            self.logger.info(f"Đã phát hiện bảng với {len(cells)} ô")
            return [table_info]  # Trả về list để hỗ trợ nhiều bảng trong tương lai

        except Exception as e:
            self.logger.error(f"Lỗi phát hiện bảng: {str(e)}")
            raise ImageError("Lỗi phát hiện bảng trong ảnh")

    def draw_table_boundaries(self, image, table_info):
        """
        Vẽ khung bảng và các ô
        Args:
            image: Ảnh gốc
            table_info: Thông tin về bảng
        Returns:
            PIL.Image: Ảnh đã vẽ khung bảng
        """
        try:
            # Chuyển đổi sang PIL Image nếu cần
            if isinstance(image, np.ndarray):
                image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

            draw_image = image.copy()
            draw = ImageDraw.Draw(draw_image)

            # Vẽ các ô
            for cell in table_info['cells']:
                bbox = cell['bbox']
                draw.rectangle(
                    [(bbox[0], bbox[1]), (bbox[2], bbox[3])],
                    outline='blue',
                    width=2
                )

            # Vẽ các đường nối giữa các ô
            if 'intersections' in table_info:
                points = np.array(table_info['intersections'])
                for i in range(len(points)):
                    for j in range(i + 1, len(points)):
                        # Vẽ đường ngang nếu cùng hàng
                        if abs(points[i][0] - points[j][0]) < 5:
                            draw.line(
                                [(points[i][1], points[i][0]),
                                 (points[j][1], points[j][0])],
                                fill='blue',
                                width=1
                            )
                        # Vẽ đường dọc nếu cùng cột
                        if abs(points[i][1] - points[j][1]) < 5:
                            draw.line(
                                [(points[i][1], points[i][0]),
                                 (points[j][1], points[j][0])],
                                fill='blue',
                                width=1
                            )

            self.logger.info("Đã vẽ khung bảng thành công")
            return draw_image

        except Exception as e:
            self.logger.error(f"Lỗi vẽ khung bảng: {str(e)}")
            return image
