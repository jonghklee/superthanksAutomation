import pyautogui

while True:
    input("마우스를 원하는 위치로 이동 후 Enter를 누르세요.")
    x, y = pyautogui.position()
    print(f"현재 마우스 좌표는: ({x}, {y})")

