import tensorflow as tf
import ray
from time import sleep
import uvicorn
import os
from starlette.applications import Starlette
from starlette.responses import UJSONResponse


num_threads = 1
concurrency = 4

cluster_addresses = {
    'ps': ["localhost:3000"],
    'worker': ["localhost:{}".format(3331 + i) for i in range(concurrency)]
}

ray.init(num_cpus=num_threads,
         object_store_memory=10 * 1000000,
         redis_max_memory=10 * 1000000)


@ray.remote(num_cpus=1 / (concurrency+1))
class ParameterServer(object):
    def __init__(self, cluster_addresses):
        self.var = tf.Variable(0.0, name='var')

        cluster = tf.train.ClusterSpec(cluster_addresses)
        server = tf.train.Server(cluster,
                                 job_name="ps",
                                 task_index=0)

        config = tf.ConfigProto()
        config.intra_op_parallelism_threads = 1
        config.inter_op_parallelism_threads = 1

        self.sess = tf.Session(target=server.target, config=config)

        print("Parameter server: initializing variables...")
        self.sess.run(tf.global_variables_initializer())
        print("Parameter server: variables initialized")


@ray.remote(num_cpus=1 / (concurrency+1))
class Worker(object):
    def __init__(self, cluster_addresses, worker_n):
        self.var = tf.Variable(0.0, name='var')

        cluster = tf.train.ClusterSpec(cluster_addresses)
        server = tf.train.Server(cluster,
                                 job_name="worker",
                                 task_index=worker_n
                                 )
        self.sess = tf.Session(target=server.target)

        print("Worker %d: waiting for cluster connection..." % worker_n)
        self.sess.run(tf.report_uninitialized_variables())
        print("Worker %d: cluster ready!" % worker_n)

        while self.sess.run(tf.report_uninitialized_variables()):
            print("Worker %d: waiting for variable initialization..." % worker_n)
            sleep(1.0)
            print("Worker %d: variables initialized" % worker_n)

    def add(self, value):
        self.sess.run(self.var.assign_add(value))
        sleep(1.0)
        return self.sess.run(self.var)


ps = ParameterServer.remote(cluster_addresses)
worker_list = [Worker.remote(cluster_addresses, worker_n)
               for worker_n in range(concurrency)]

app = Starlette(debug=False)
num_requests = 0

@app.route('/', methods=['GET'])
async def homepage(request):
    params = request.query_params
    value = params.get('value', 1)

    # Round-robin the Workers to distribute the load
    global num_requests
    worker = worker_list[num_requests % concurrency]
    num_requests += 1

    result = ray.get(worker.add.remote(value))

    return UJSONResponse({'text': result})

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
