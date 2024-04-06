from pdf2image import convert_from_path, convert_from_bytes

images = convert_from_bytes(open('D:/python/C_강동우_2000938728.pdf', 'rb').read())

for idx, img in enumerate(images):
    img.save('pdf_' + str(idx).zfill(len(str(len(images)))) + '.jpg', 'JPEG') # pdf_넘버링.jpg 이런 방식으로 네이밍을 합니다.

#with tempfile.TemporaryDirectory() as path:
#    images_from_path = convert_from_path('/home/belval/example.pdf', output_folder=path)
    # Do something herecls
    #


