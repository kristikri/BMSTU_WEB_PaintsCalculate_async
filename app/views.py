from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
import time
import random
import requests
from concurrent import futures

MAIN_SERVICE_URL = "http://localhost:8080/api/v1"
AUTH_TOKEN = "secret123"

executor = futures.ThreadPoolExecutor(max_workers=5)

def calculate_paint_quantity_single(request_id, paint_id, hiding_power, area, layers):
    """
    Асинхронный расчёт количества краски для одной записи request_paint.
    """
    try:
        calculation_time = random.randint(5, 10)
        print(
            f"Начинаем расчёт: request={request_id}, paint={paint_id} "
            f"(ожидание {calculation_time} секунд)"
        )
        time.sleep(calculation_time)

        if area > 0 and layers > 0 and hiding_power > 0:
            quantity = round((area * layers* hiding_power)/1000, 3)
            success = True
            print(f"Результат: paint={paint_id}, quantity={quantity}")
        else:
            quantity = 0
            success = False
            print(f"Ошибка расчёта: неверные параметры (area={area}, layers={layers})")

        return {
            "request_id": request_id,
            "paint_id": paint_id,
            "quantity": quantity,
            "success": success,
            "calculation_time": calculation_time,
        }

    except Exception as e:
        print(f"Ошибка при расчёте краски {paint_id}: {e}")
        return {
            "request_id": request_id,
            "paint_id": paint_id,
            "quantity": 0,
            "success": False,
            "error": str(e),
        }

def send_calculation_result(task):
    try:
        result = task.result()

        print(
            f"Отправка результата: request={result['request_id']}, paint={result['paint_id']}, "
            f"quantity={result['quantity']}"
        )

        if result["success"]:
            update_url = (
                f"{MAIN_SERVICE_URL}/requests/{result['request_id']}/paint_quantity"
            )

            payload = {
                "paint_id": result["paint_id"],
                "quantity": result["quantity"],
            }

            headers = {
                "Authorization": AUTH_TOKEN,
                "Content-Type": "application/json",
            }

            response = requests.put(update_url, json=payload, headers=headers, timeout=10)

            print(f"Ответ Go-сервера: {response.status_code}")
            print("Тело:", response.text)

        else:
            print(f"Расчёт не удался для краски {result['paint_id']}")

    except Exception as e:
        print(f"Ошибка отправки данных в основной сервис: {e}")


@api_view(["POST"])
def calculate_quantity(request):
    required_fields = ["request_id", "paint_id", "hiding_power", "area", "layers"]

    if all(field in request.data for field in required_fields):
        request_id = request.data["request_id"]
        paint_id = request.data["paint_id"]
        hiding_power = request.data["hiding_power"]
        area = request.data["area"]
        layers = request.data["layers"]

        print(
            f"Запрос на расчёт: request={request_id}, paint={paint_id}, "
            f"hiding_power={hiding_power}, area={area}, layers={layers}"
        )

        task = executor.submit(
            calculate_paint_quantity_single,
            request_id,
            paint_id,
            hiding_power,
            area,
            layers,
        )
        task.add_done_callback(send_calculation_result)

        return Response(
            {
                "message": "Расчёт количества краски запущен",
                "request_id": request_id,
                "paint_id": paint_id,
                "estimated_time": "5-10 секунд",
            },
            status=status.HTTP_202_ACCEPTED,
        )

    return Response(
        {"error": "Не все необходимые поля получены"},
        status=status.HTTP_400_BAD_REQUEST,
    )

@api_view(["GET"])
def health_check(request):
    return Response(
        {"status": "healthy", "service": "async-paint-quantity-calculator"},
        status=status.HTTP_200_OK,
    )
