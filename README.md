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

Результаты нагрузочного тестирования:  
ab -n 50000 -c 100 http://127.0.0.1/  
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

Document Path:          /  
Document Length:        0 bytes  

Concurrency Level:      100  
Time taken for tests:   135.220 seconds  
Complete requests:      50000  
Failed requests:        0  
Non-2xx responses:      50000  
Total transferred:      8100000 bytes  
HTML transferred:       0 bytes  
Requests per second:    369.77 [#/sec] (mean)  
Time per request:       270.440 [ms] (mean)  
Time per request:       2.704 [ms] (mean, across all concurrent requests)  
Transfer rate:          58.50 [Kbytes/sec] received  

Connection Times (ms)  
              min  mean[+/-sd] median   max  
Connect:        0   21 428.5      0    9799  
Processing:     1  249 357.3    199    5948  
Waiting:        1  248 355.7    199    5948  
Total:          1  270 552.8    200    9804  

Percentage of the requests served within a certain time (ms)  
  50%    200  
  66%    208  
  75%    213  
  80%    217  
  90%    229  
  95%    549  
  98%    955  
  99%   1326  
 100%   9804 (longest request)  
