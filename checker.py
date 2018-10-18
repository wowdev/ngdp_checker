import itertools
import math
import multiprocessing
import threading
import pycurl
import tqdm
import string

from keg import ribbit

regions = ["eu", "us"]
endpoints = ["cdns", "versions", "bgdl", "blobs", "blob/install", "blob/game"]

cores = multiprocessing.cpu_count()
workers_per_core = 1

valid_programs = []
error_404 = 0
error_other = 0

def load(filename):
    with open(filename) as file:
        return [line.strip() for line in file.readlines()]

def split(iterable, n):
    sentinel=object()
    return ((entry for entry in iterable if entry is not sentinel)
            for iterable in itertools.zip_longest(*[iter(iterable)]*n, fillvalue=sentinel))

def check(url, retry = 5):
    try: 
        print(f"Checking url: {url}")
        response = ribbit.get(url)
    except:
        if retry > 0:
            return check(url, retry - 1)
        else:
            return -1

    return 200


def worker(items):
    global valid_programs

    worker_programs = []

    for item in items:
        global error_404
        global error_other
        (program, url) = item

        if program in valid_programs:
            #pbar.update(1)
            continue

        try:
            code = check(url)
            if code == 200:
                worker_programs.append(program)
            elif code == 404:
                error_404 += 1
            else:
                error_other += 1
        except Exception as e:
            pass
        finally:
            #pbar.update(1)
    
    valid_programs += worker_programs

projects = load("known_projects.txt")
suffices = load("known_suffices.txt") #+ list(string.ascii_lowercase) + list(string.digits)
suffices_squared = map(''.join, itertools.product(suffices, repeat=2))

hosts = map(lambda region: f"ribbit://{region}.patch.battle.net", regions)
guesses = map(''.join, itertools.product(projects, suffices_squared))
items = set(map(lambda it: (it[1], '/'.join(it)), itertools.product(hosts, guesses, endpoints)))
batch_size = math.ceil(len(items) / (cores * workers_per_core))
batches = split(items, batch_size)

#pbar = tqdm.tqdm(total=len(items))

threads = []
for batch in batches:
    thread = threading.Thread(target=worker, args=(batch,))
    thread.daemon = True
    thread.start()

    threads.append(thread)

for thread in threads:
    thread.join()

#pbar.close()

print("Found valid urls:", len(valid_programs))
print("Encountered 404s:", error_404)
print("Encountered errors:", error_other)
print("Found program codes:")

for program in set(valid_programs):
    print(program)
