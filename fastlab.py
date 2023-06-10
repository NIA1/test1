import fastapi.responses
import numpy
import io
from PIL import Image
from PIL import ImageDraw
import matplotlib.pyplot as plt
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
app = FastAPI()
def sum_two_args(x,y):
 return x+y
# Hello World route
@app.get("/")
def read_root():
 return {"Hello": "World"}
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
# возвращаем some.html, сгенерированный из шаблона
# передав туда одно значение something
@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
 return templates.TemplateResponse("some.html", {"request": request, "something": something})
def create_some_image(some_difs):
 imx = 200
 imy = 200
 image = numpy.zeros((imx,imy, 3), dtype=numpy.int8)
 image[0:imy//2,0:imx//2,0] = some_difs
 image[imy//2:,imx//2:,2] = 240
 image[imy//2:,0:imx//2, 1] = 240
 return image
# возврат изображения в виде потока медиаданных по URL
@app.get("/bimage", response_class=fastapi.responses.StreamingResponse)
async def b_image(request: Request):
 # рисуем изображение, сюда можете вставить GAN, WGAN сети и т. д.
 # взять изображение из массива в Image PIL
 image = create_some_image(100)
 im = Image.fromarray(image, mode="RGB")
 # сохраняем изображение в буфере оперативной памяти
 imgio = io.BytesIO()
 im.save(imgio, 'JPEG')
 imgio.seek(0)
 # Возвращаем изображение в виде mime типа image/jpeg
 return fastapi.responses.StreamingResponse(content=imgio, media_type="image/jpeg")
# возврат двух изображений в таблице html, одна ячейка ссылается на url bimage
# другая ячейка указывает на файл из папки static по ссылке
# при этом файл туда предварительно сохраняется после генерации из массива
@app.get("/image", response_class=HTMLResponse)
async def make_image(request: Request):
 image_n = "image.jpg"
 image_dyn = request.base_url.path+"bimage"
 image_st = request.url_for("static", path = f'/{image_n}')
 image = create_some_image(250)
 im = Image.fromarray(image, mode="RGB")
 im.save(f"./static/{image_n}")
 # передаем в шаблон две переменные, к которым сохранили url
 return templates.TemplateResponse("image.html", {"request": request, "im_st":image_st, "im_dyn": image_dyn})

def draw_cross(imgg, color, number_op):
 is_horizontal = number_op
 if is_horizontal == 'True':
  is_horizontal = True
 elif is_horizontal == 'False':
  is_horizontal = False
 else:
  print("Type True or False")
  return

 img = imgg.copy()
 img_input = imgg

 if is_horizontal:
  draw = ImageDraw.Draw(img)
  # Рисуем горизонтальный крест
  shape1 = [(0, 90),(200, 110)]
  draw.ellipse(shape1, fill=color, outline=(0, 0, 0))
  shape2 = [(90, 40), (110, 160)]
  draw.ellipse(shape2, fill=color, outline=(0, 0, 0))
  # img.show()
 else:
  draw = ImageDraw.Draw(img)
  # Рисуем вертикальный крест
  shape1 = [(90, 0), (110, 200)]
  draw.ellipse(shape1, fill=color, outline=(0, 0, 0))
  shape2 = [(40, 90), (160, 110)]
  draw.ellipse(shape2, fill=color, outline=(0, 0, 0))
 # выводим начальную и конечную картинки
 fig, axs = plt.subplots(2,2)
 axs[0,0].imshow(img_input)
 axs[0,1].imshow(img)
 axs[0,0].axis('off')
 axs[0,1].axis('off')
 # строим гистограмму распредения цветов начальной картинки
 r, g, b = img_input.split()
 colors = ('r', 'g', 'b')
 for channel, color in zip((r, g, b), colors):
  axs[1,0].hist(numpy.array(channel).ravel(), bins=256, color=color, alpha=0.5)
 # строим гистограмму распределения цветов конечной картинки
 r, g, b = img.split()
 colors = ('r', 'g', 'b')
 for channel, color in zip((r, g, b), colors):
  axs[1,1].hist(numpy.array(channel).ravel(), bins=256, color=color, alpha=0.5)
 img.save("./output.jpg",'JPEG')
 plt.savefig("static/result.jpg")
 return fig

from fastapi import Form, File, UploadFile
from typing import List
import hashlib
from PIL import ImageDraw
@app.post("/image_form", response_class=HTMLResponse)
async def make_image(request: Request,
            name_op:str = Form(),
            number_op:str = Form(),
            r:int = Form(),
            g:int = Form(),
            b:int = Form(),
            files: List[UploadFile] = File(description="Multiple files as UploadFile")
            ):
 # устанавливаем готовность прорисовки файлов, можно здесь проверить, что файлы вообще есть
 # лучше использовать исключения
 ready = False
 print(len(files))
 if(len(files)>0):
  if(len(files[0].filename)>0):
   ready = True
 images = []
 if ready:
  print([file.filename.encode('utf-8') for file in files])
  # преобразуем имена файлов в хеш -строку
  images = ["static/"+hashlib.sha256(file.filename.encode('utf-8')).hexdigest() for file in files]
  # берем содержимое файлов
  content = [await file.read() for file in files]
  # создаем объекты Image типа RGB размером 200 на 200
  p_images = [Image.open(io.BytesIO(con)).convert("RGB").resize((200,200)) for con in content]
  # сохраняем изображения в папке static
  for i in range(len(p_images)):
   img = p_images[i]
   figures = draw_cross(img,(r,g,b), number_op)
   image = Image.open("static/result.jpg")
   #image = ["static/"+hashlib.sha256(file.filename.encode('utf-8')).hexdigest() for file in files]
   # p_images[i].save("./"+images[i],'JPEG')
  # возвращаем html с параметрами-ссылками на изображения, которые позже будут
  # извлечены браузером запросами get по указанным ссылкам в img src
  return templates.TemplateResponse("forms.html", {"request": request, "ready": ready, "images": image})
@app.get("/image_form", response_class=HTMLResponse)
async def make_image(request: Request):
 return templates.TemplateResponse("forms.html", {"request": request})
