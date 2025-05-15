import cv2
import qrcode
import datetime
import pandas as pd
import os
from pyzbar.pyzbar import decode, ZBarSymbol
from records import records

class QR_GEN():
    def __init__(self, names_csv):
        self.record = []
        self.qr_list = []
        self.names_csv = names_csv
        self.df = pd.read_csv(self.names_csv)

    def createQrCode(self, save=True):
        df = pd.read_csv(self.names_csv)

        if not os.path.exists("QRs"):
            os.makedirs("QRs")

        for index, values in df.iterrows():
            name = values["Name"]
            roll = values["Roll"]
            data = f"{name} {roll}"
            self.record.append(data)
            image = qrcode.make(data)
            self.qr_list.append(f"{roll}_{name}.jpg")
            if save:
                image.save(os.path.join("QRs", f"{roll}_{name}.jpg"))
        return self.record

    def name_col_check(self, filename):
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        self.df = pd.read_csv(self.names_csv)
        if date not in self.df.columns:
            self.df.insert(2, column=date, value="A")
            self.df.to_csv(filename, index=True)
        return date

    # def qr_check_attendance(self, img):
    #     date = self.name_col_check("attendance.csv")
    #     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #     decoded_qr = decode(gray, symbols=[ZBarSymbol.QRCODE])

    #     if decoded_qr:
    #         for qr in decoded_qr:
    #             myData = qr.data.decode('utf-8')
    #             scanedname, scanedroll = myData.split(" ")
    #             if myData in records:
    #                 print(f"Good morning, {scanedname}. Your attendance has been marked.")
    #                 self.df = pd.read_csv('attendance.csv')
    #                 pos = self.df[self.df['Name'] == scanedname].index.values
    #                 self.df.loc[pos[0], date] = "P"
    #                 self.df.to_csv('attendance.csv', index=True)

    def qr_check_attendance(self, img):
        date = datetime.datetime.now().strftime("%d-%m-%Y")
        
        if not os.path.exists("attendance.csv"):
            self.df.to_csv("attendance.csv", index=False)

        self.df = pd.read_csv('attendance.csv')

        # Add date column if not present
        if date not in self.df.columns:
            self.df[date] = "A"  # Mark all absent by default

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        decoded_qr = decode(gray, symbols=[ZBarSymbol.QRCODE])

        if decoded_qr:
            for qr in decoded_qr:
                myData = qr.data.decode('utf-8')
                scanedname, scanedroll = myData.split(" ")
                if myData in records:
                    print(f"✅ Good morning, {scanedname}. Your attendance has been marked.")

                    pos = self.df[self.df['Name'] == scanedname].index.values
                    if len(pos) > 0:
                        self.df.loc[pos[0], date] = "P"
                        self.df.to_csv('attendance.csv', index=False)


    def qr_check_mid_day_meal(self, img):
        date = self.name_col_check("mid-day-meal.csv")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        decoded_qr = decode(gray, symbols=[ZBarSymbol.QRCODE])

        if decoded_qr:
            for qr in decoded_qr:
                myData = qr.data.decode('utf-8')
                scanedname, scanedroll = myData.split(" ")
                if myData in records:
                    print(f"Hello, {scanedname}. Your meal will be served.")
                    self.df = pd.read_csv('mid-day-meal.csv')
                    pos = self.df[self.df['Name'] == scanedname].index.values
                    self.df.loc[pos[0], date] = "Received"
                    self.df.to_csv('mid-day-meal.csv', index=True)

    def plot_polygon(self, img, polygon_cords, r=5, len=34, th=4, clr=(0, 255, 0)):
        top_left, top_right, bottom_left, bottom_right = polygon_cords[:4]
        cv2.circle(img, top_left, radius=r, color=clr, thickness=-1)
        cv2.line(img, top_left, (top_left[0], top_left[1] + len), color=clr, thickness=th)
        cv2.line(img, top_left, (top_left[0] + len, top_left[1]), color=clr, thickness=th)
        cv2.circle(img, top_right, radius=r, color=clr, thickness=-1)
        cv2.line(img, top_right, (top_right[0], top_right[1] - len), color=clr, thickness=th)
        cv2.line(img, top_right, (top_right[0] + len, top_right[1]), color=clr, thickness=th)
        cv2.circle(img, bottom_left, radius=r, color=clr, thickness=-1)
        cv2.line(img, bottom_left, (bottom_left[0], bottom_left[1] - len), color=clr, thickness=th)
        cv2.line(img, bottom_left, (bottom_left[0] - len, bottom_left[1]), color=clr, thickness=th)
        cv2.circle(img, bottom_right, radius=r, color=clr, thickness=-1)
        cv2.line(img, bottom_right, (bottom_right[0], bottom_right[1] + len), color=clr, thickness=th)
        cv2.line(img, bottom_right, (bottom_right[0] - len, bottom_right[1]), color=clr, thickness=th)
        return img


def main():
    gen = QR_GEN("names.csv")
    gen.createQrCode(save=True)

    cap = cv2.VideoCapture(0)  # Using the default webcam

    try:
        while True:
            res, img = cap.read()
            if not res:
                print("Error: Unable to read from webcam.")
                break

            img = cv2.resize(img, (640, 480))

            # Ensure image is valid before processing
            if img is None:
                print("Error: Captured image is None.")
                continue

            # Convert to grayscale for better QR detection
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # Decode QR codes
            decoded_qr = decode(gray, symbols=[ZBarSymbol.QRCODE])

            if decoded_qr:
                gen.qr_check_mid_day_meal(img)
                polygon_cords = decoded_qr[0].polygon
                img = gen.plot_polygon(img, polygon_cords)

            cv2.imshow("Webcam", img)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except KeyboardInterrupt:
        print("\nProcess interrupted by user.")

    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
