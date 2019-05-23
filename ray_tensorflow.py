import tensorflow as tf
import ray
from time import sleep
import asyncio
from ray.experimental import async_api

num_threads = 1
concurrency = 4

cluster_addresses = {
    'ps': ["localhost:3000"],
    'worker': ["localhost:{}".format(3331 + i) for i in range(concurrency)]
}

ray.init(num_cpus=num_threads,
         object_store_memory=10 * 1000000,
         redis_max_memory=10 * 1000000)


@ray.remote(num_cpus=num_threads / (concurrency+1))
class ParameterServer(object):
    def __init__(self, cluster_addresses, num_threads):

        cluster = tf.train.ClusterSpec(cluster_addresses)

        with tf.device("/job:ps/task:0"):
            self.var = tf.Variable(0.0, name='var')

        config = tf.ConfigProto()
        config.intra_op_parallelism_threads = num_threads
        config.inter_op_parallelism_threads = num_threads

        server = tf.train.Server(cluster,
                                 job_name="ps",
                                 task_index=0)
        self.sess = tf.Session(target=server.target, config=config)

        print("Parameter server: initializing variables...")
        self.sess.run(tf.global_variables_initializer())
        print("Parameter server: variables initialized")


@ray.remote(num_cpus=num_threads / (concurrency+1))
class Worker(object):
    def __init__(self, cluster_addresses, worker_n):
        with tf.device("/job:ps/task:0"):
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
        print(self.sess.run(self.var))


ps = ParameterServer.remote(cluster_addresses, num_threads)
worker_list = [Worker.remote(cluster_addresses, i) for i in range(concurrency)]

loop = asyncio.get_event_loop()
tasks = [async_api.as_future(worker.add.remote(value))
         for value, worker in enumerate(worker_list)]
loop.run_until_complete(
    asyncio.gather(*tasks))
