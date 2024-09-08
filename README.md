# titler
a shitty python app to help me rename my pdf collection(s) somewhat faster...

Ideally it works by pulling metadata from the pdfs, if that fails it uses the NuExtract model to read the first page of text and suggest a title, if you don't like the suggestion you can type one in yourself.

# requirements:
- a beefy rig
- poetry
- python3.11
- pytorch (if using the local_v1.py) [recommended]
- ollama ( if using it to run the models) [this will eventually replace the local_v1.py]

# usage:
![output.png](output.png)


```sh
poetry run python local_v1.py --input /home/jer/Documents/go/scrapeThisFor/output/paper.pdf
```

or [eventually...]
```sh
# In one terminal:
ollama pull llama3:latest
ollama serve

# In another terminal:
poetry run python main.py --input /home/jer/Documents/go/scrapeThisFor/output/paper.pdf
```

# Notes:
first time usage may be very tedious as models need to download etc.