# File: butlar/views.py
# Author: Suhani Mitra (suhanim@bu.edu), 3/27/2025

from django.db.models.query import QuerySet
from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.db.models import Count, Sum, Q
import time

# Create your views here.
def ButlarHome(request):
    if request.method == "POST":
        # Run your command: stream audio, process with voice_assistant.py
        cmd = "./miniaudio_stream | sox -t raw -r 16000 -e signed -b 16 -c 2 - -t raw -r 16000 -e signed -b 16 -c 1 - | python3 /path/to/voice_assistant.py"
        
        # Use shell=True only because it includes pipes — safe here since input is hardcoded
        process = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True
        )

        def stream_output():
            for line in process.stdout:
                yield f"data: {line.strip()}\n\n"  # Server-Sent Event format

        return StreamingHttpResponse(stream_output(), content_type="text/event-stream")
    
    return render(request, "butlar/base.html")


def butlar_interface(request):
    return render(request, "butlar/butlar_interface.html")

    