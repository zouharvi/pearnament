"""
This script tests Pearmut and Appraise speeds, used in the Pearmut report.
"""

# %%

# pearmut

import requests
import time
import statistics
import scipy.stats

def measure_average_response(
    url,
    payload=None,
    method="post",
    iterations=1,
    cookies=None,
):
    response_times = []

    # Use a Session to persist the TCP connection (keep-alive)
    with requests.Session() as session:
        if cookies:
            session.cookies.update(cookies)

        for i in range(iterations):
            start_time = time.perf_counter()

            # Perform the POST request
            if method.lower() == "get":
                response = session.get(url, params=payload)
            elif method.lower() == "post":
                response = session.post(url, json=payload)
            else:
                raise ValueError(f"Unsupported method: {method}")

            assert (
                response.status_code == 200
            ), f"Request failed with status code {response.status_code}"
            response_times.append(time.perf_counter() - start_time)

    # Calculate results
    print(url)
    mean = statistics.mean(response_times)
    print(f"{mean*1000:.1f}ms")
    # compute 95% confidence interval
    ci = scipy.stats.t.interval(
        0.99,
        len(response_times) - 1,
        loc=mean,
        scale=scipy.stats.sem(response_times),
    )
    print(f"  ±{(ci[1]-ci[0])/2*1000:.1f}ms (99% CI)")

# %%

appraise_csrf_cookie = input()
pearmut_token_ensk = input()

# %%

measure_average_response(
    url="http://localhost:8001/basic.html",
    method="get",
    iterations=100,
)

measure_average_response(
    url="http://localhost:8001/get-next-item",
    payload={"campaign_id": "abc_ensk", "user_id": "ensk1"},
    iterations=100,
)


measure_average_response(
    url="http://localhost:8001/dashboard.html",
    method="get",
    iterations=100,
)

measure_average_response(
    url="http://localhost:8001/dashboard-data",
    method="post",
    payload={"campaign_id": "abc_ensk", "token": pearmut_token_ensk},
    iterations=100,
)

measure_average_response(
    url="http://localhost:8001/dashboard-results",
    method="post",
    payload={"campaign_id": "abc_ensk", "token": pearmut_token_ensk},
    iterations=100,
)

measure_average_response(
    url="http://localhost:8001/download-annotations",
    method="get",
    payload={"campaign_id": "abc_ensk", "token": pearmut_token_ensk},
    iterations=100,
)

# %%


measure_average_response(
    url="http://localhost:8000/direct-assessment-document/",
    method="get",
    iterations=100,
    cookies={"csrftoken": appraise_csrf_cookie},
)


measure_average_response(
    url="http://localhost:8000/campaign-status/abc24/",
    method="get",
    iterations=100,
)

# %%

def measure_average_response_chill(*args, **kwargs):
    time.sleep(10)  # wait for server/connector to chill
    return measure_average_response(*args, **kwargs)


measure_average_response_chill(
    url="https://pearmut.ngrok.io/basic.html",
    method="get",
    iterations=100,
)

measure_average_response_chill(
    url="https://pearmut.ngrok.io/get-next-item",
    payload={"campaign_id": "abc_ensk", "user_id": "ensk1"},
    iterations=100,
)

measure_average_response_chill(
    url="https://pearmut.ngrok.io/dashboard.html",
    method="get",
    iterations=100,
)

measure_average_response_chill(
    url="https://pearmut.ngrok.io/dashboard-data",
    method="post",
    payload={"campaign_id": "abc_ensk", "token": pearmut_token_ensk},
    iterations=100,
)

measure_average_response_chill(
    url="https://pearmut.ngrok.io/dashboard-results",
    method="post",
    payload={"campaign_id": "abc_ensk", "token": pearmut_token_ensk},
    iterations=100,
)

# %%

measure_average_response_chill(
    url="https://pearmut.ngrok.io/download-annotations",
    method="get",
    payload={"campaign_id": "abc_ensk", "token": pearmut_token_ensk},
    iterations=100,
)

measure_average_response_chill(
    url="https://alani-unpleadable-vindicatedly.ngrok-free.dev/direct-assessment-document/",
    cookies={"csrftoken": appraise_csrf_cookie},
    method="get",
    iterations=100,
)

measure_average_response_chill(
    url="https://alani-unpleadable-vindicatedly.ngrok-free.dev/campaign-status/abc24/",
    method="get",
    iterations=100,
)

# %%
# run bash command 100 times

import subprocess
start_time = time.perf_counter()
subprocess.run(
    "cd ~/Appraise; for _ in {1..100}; do python3 manage.py ExportSystemScoresToCSV abc24 > /dev/null; done",
    shell=True,
    check=True
)
print("Appraise export", f"{(time.perf_counter() - start_time)/100*1000:.1f}ms", "", sep="\n")
