# TensorFlow Prediction Multiprocess w/ Ray

A proof of concept on how to use TensorFlow for prediction tasks in a multiprocess setting with a few important features:

* Can run all processes in a single thread and single machine. (e.g. good for [Cloud Run](https://cloud.google.com/run/) which may be limited to 1 vCPU)
* Can run worker tasks asynchronously via `asyncio`. (e.g. model prediction)
* Creates a single TensorFlow Session/Model to be shared by the worker processes w/ between-graph replication. (especially important if using a GPU!)

This POC leverages [ray](https://github.com/ray-project/ray) for its multiprocessing/colocation capabilities and Distributed TensorFlow for its session management (this is essentially a port of Matthew Rahtz's [Distributed TensorFlow Hello World](https://github.com/mrahtz/distributed_tensorflow_gentle_introduction) w/ ray + a few Pythonic improvements). It is incredibly hacky, but it is necessary since `tf.Session()` does not play nice with multiple threads and/or processes.

Note: will likely not work with Python wrappers (including Jupyter Notebooks, Anaconda, and Server Process Managers), and the async may not work with existing async apps.

## Files

* `ray_tensorflow.py`: Single script for running multiple TensorFlow workers on a single thread, but can be configured to use more threads for proportionate performance increase. The script adds the `worker_id` value on each `Worker` to a sum on the `ParameterServer`.
* `ray_tensorflow_flask.py`: Simple Flask app which allows parallel predictioning using round-robin queuing (adds a user-provided `value` to a persistant sum). The app can handle concurrent requests in threaded mode, which admittingly reduces the impact of the implementation.
* `ray_tensorflow_starlette.py`: Prototype of the Flask app which doesn't use async ray due to the event loop issues, and as a result is less effective.

## Maintainer/Creator

Max Woolf ([@minimaxir](https://minimaxir.com))

*Max's open-source projects are supported by his [Patreon](https://www.patreon.com/minimaxir). If you found this project helpful, any monetary contributions to the Patreon are appreciated and will be put to good creative use.*

## License

MIT
