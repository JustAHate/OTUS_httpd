# OTUS_httpd web server

Веб сервер для раздачи статики  

## Getting Started

Запуск: python3 httpd.py  

Опциональные параметры:  
-i (--ip) - ip адрес на котором будет запущен веб сервер  
-p (--port) - порт на котором будет запущен веб сервер  
-l (--log) - для указания пути до файла логирования  
-r (--root) - корневая директория для веб сервера  
-w (--workers) - количество воркеров запускаемых веб сервером  

## Description

При запуске создается пул из N тредов, которые слушают очередь (queue.Queue()) и ждут от нее запросов.

Результаты нагрузочного тестирования(бэклог - 100, воркеры - 50):  
ab -n 50000 -c 100 http://127.0.0.1/test.txt  
This is ApacheBench, Version 2.3 <$Revision: 1843412 $>  
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/  
Licensed to The Apache Software Foundation, http://www.apache.org/  


Benchmarking 127.0.0.1 (be patient)  
Completed 5000 requests  
Completed 10000 requests  
Completed 15000 requests  
Completed 20000 requests  
Completed 25000 requests  
Completed 30000 requests  
Completed 35000 requests  
Completed 40000 requests  
Completed 45000 requests  
Completed 50000 requests  
Finished 50000 requests  


Server Software:        Otus  
Server Hostname:        127.0.0.1  
Server Port:            80  

Document Path:          /test.txt  
Document Length:        12 bytes  

Concurrency Level:      100  
Time taken for tests:   134.803 seconds  
Complete requests:      50000  
Failed requests:        0  
Total transferred:      7650000 bytes  
HTML transferred:       600000 bytes  
Requests per second:    370.91 [#/sec] (mean)  
Time per request:       269.607 [ms] (mean)  
Time per request:       2.696 [ms] (mean, across all concurrent requests)  
Transfer rate:          55.42 [Kbytes/sec] received  

Connection Times (ms)  
              min  mean[+/-sd] median   max  
Connect:        0  144 1846.6      0   25987  
Processing:     1  125 116.5    112    1679  
Waiting:        1  125 115.9    112    1679  
Total:          1  269 1845.2    113   25991  

Percentage of the requests served within a certain time (ms)  
  50%    113  
  66%    116  
  75%    118  
  80%    120  
  90%    126  
  95%    133  
  98%    528  
  99%    939  
 100%  25991 (longest request)  
