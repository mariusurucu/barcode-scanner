import argparse
import sys
import cv2
import datetime

import os

import barcode_scanner_image as bsi

from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QDialog, QApplication, QFileDialog
from PyQt5.uic import loadUi
from pyzbar import pyzbar


class barcode(QDialog):
    def __init__(self):
        super(barcode, self).__init__()
        loadUi('barcode.ui', self)

        # construct the argument parser and parse the arguments
        ap = argparse.ArgumentParser()
        ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                        help="path to output CSV file containing barcodes")
        args = vars(ap.parse_args())
        self.csv = open(args["output"], "w")
        self.found = set()

        self.image = None
        self.image_frame = None
        self.timerChecker = False

        self.ImageScan.clicked.connect(self.image_scan)
        self.WebScan.clicked.connect(self.web_scan)
        self.ShowDoc.clicked.connect(self.show_doc)

    def image_scan(self):
        try:
            self.timerChecker = self.timer.isActive()
            if self.timerChecker:
                self.timer.stop()
        except:
            pass

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()", "",
                                                  "All Files (*);;Python Files (*.py)", options=options)
        if fileName:
            print(fileName)
            self.image_frame = bsi.scanner(fileName)
            self.display_web(self.image_frame, 1)

    def show_doc(self):
        os.startfile('barcodes.csv')

    def web_scan(self):

        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(0)

    def update_frame(self):
        ret, self.image = self.capture.read()

        # find the barcodes in the frame and decode each of the barcodes
        barcodes = pyzbar.decode(self.image)

        # loop over the detected barcodes
        for bar in barcodes:
            # extract the bounding box location of the barcode and draw
            # the bounding box surrounding the barcode on the image
            (x, y, w, h) = bar.rect
            cv2.rectangle(self.image, (x, y), (x + w, y + h), (0, 0, 255), 2)

            # the barcode data is a bytes object so if we want to draw it
            # on our output image we need to convert it to a string first
            barcodeData = bar.data.decode("utf-8")
            barcodeType = bar.type

            # draw the barcode data and barcode type on the image
            text = "{} ({})".format(barcodeData, barcodeType)
            cv2.putText(self.image, text, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # if the barcode text is currently not in our CSV file, write
            # the timestamp + barcode to disk and update the set
            if barcodeData not in self.found:
                self.csv.write("{},{}\n".format(datetime.datetime.now(),
                                                barcodeData))
                self.csv.flush()
                self.found.add(barcodeData)

        # self.image = cv2.flip(self.image, 1)
        self.display_web(self.image, 1)

    def display_web(self, img, window=1):
        qformat = QImage.Format_Indexed8
        if len(img.shape) == 3:
            if img.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888

        outImage = QImage(img, img.shape[1], img.shape[0], img.strides[0], qformat)
        outImage = outImage.rgbSwapped()

        if window == 1:
            self.label.setPixmap(QPixmap.fromImage(outImage))
            self.label.setScaledContents(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = barcode()
    window.setWindowTitle('Analiza barcode')
    window.show()
    sys.exit(app.exec_())
