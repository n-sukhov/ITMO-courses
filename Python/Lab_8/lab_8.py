#1 вариант
import cv2

#1 задание
def convert_to_grayscale(image_path, save_path):
    image = cv2.imread(image_path)
    grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(save_path, grayscale_image)
    print(f"Изображение сохранено: {save_path}")

#2 задание
def track_marker(camera_index, marker_path):
    marker = cv2.imread(marker_path, cv2.IMREAD_GRAYSCALE)
    if marker is None:
        print("Невереный путь к файлу с маркером.\n")
        return

    _, marker_thresh = cv2.threshold(marker, 110, 255, cv2.THRESH_BINARY)
    marker_contours, _ = cv2.findContours(marker_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(marker_contours) == 0:
        print("Не удалось найти контур маркера.\n")
        return

    marker_contour = max(marker_contours, key=cv2.contourArea)

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Нет доступа к камере.\n")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, frame_thresh = cv2.threshold(gray_frame, 110, 255, cv2.THRESH_BINARY)
        frame_contours, _ = cv2.findContours(frame_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        matches = []
        for contour in frame_contours:
            matches.append(cv2.matchShapes(marker_contour, contour, cv2.CONTOURS_MATCH_I1, 0))

        if min(matches) < 0.05:
            contour = frame_contours[matches.index(min(matches))]
            x, y, w, h = cv2.boundingRect(contour)
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            center_x = x + w // 2
            center_y = y + h // 2

            cv2.putText(frame, f"Center: ({center_x}, {center_y})", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)


        cv2.imshow("frame", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()



if __name__ == '__main__':
    convert_to_grayscale('Lab_8/variant-1.jpg', 'Lab_8/variant-1-grayscale.jpg')
    track_marker(0, 'Lab_8/ref-point.jpg')
