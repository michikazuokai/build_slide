from PIL import Image
import pyautogui

# 画面全体のスクリーンショット
screenshot = pyautogui.screenshot()

# トリミング領域（左上x, y, 右下x, y）
crop_area = (590, 730, 2350, 1770)
cropped = screenshot.crop(crop_area)

# 保存
cropped.save("/Users/michikazuokai/Documents/s1.png")