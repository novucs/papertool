from concurrent.futures.thread import ThreadPoolExecutor

import jinja2
from flask import (
    Flask,
    request,
)

executor = ThreadPoolExecutor()
papers = [
    # "ADAM: A METHOD FOR STOCHASTIC OPTIMIZATION",
    # "The Option-Critic Architecture",
    # "Data-Efficient Hierarchical Reinforcement Learning",
    # "Addressing Function Approximation Error in Actor-Critic Methods",
    # "REINFORCEMENT LEARNING WITH UNSUPERVISED AUXILARY TASKS",
    # "CONTINUOUS CONTROL WITH DEEP REINFORCEMMENT LEARNING",
    # "Asynchronous Methods for Deep Reinforcement Learning",
    # "Hindsight Experience Replay",
    # "The Ising model on a dynamically triangulated disk with a boundary magnetic field",
    "dqn paper",
]

# from papertool.scraper import scrape_paper
#
# refs = scrape_paper(papers[0], executor)

app = Flask(__name__)
jinja2_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(searchpath="./templates"))


@app.route('/')
def home():
    return jinja2_environment.get_template("index.html").render()


@app.route('/search')
def search():
    print(request.data)
    return 'hi'


app.run(host='0.0.0.0', port=8080)
