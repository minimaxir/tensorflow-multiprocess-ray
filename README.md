# TensorFlow Prediction Multiprocess w/ Ray

A proof of concept on how to use TensorFlow in a multiprocess setting with a few important features:

* Can run all processes in a single thread and single machine. (e.g. good for Cloud Run)
* Can run worker tasks asynchronously via `asyncio`. (e.g. model prediction)
* Creates a single TensorFlow Session/Model to be shared by a worker thread.

This POC leverages [ray](https://github.com/ray-project/ray) for its multiprocessing capabilities and Distributed TensorFlow for its session management (this is essentially a port of Matthew Rahtz's [Distributed TensorFlow Hello World](https://github.com/mrahtz/distributed_tensorflow_gentle_introduction) w/ ray). It is incredibly hacky, but it is necessary since `tf.Session()` does not play nice with multiple threads and/or processes.

## Maintainer/Creator

Max Woolf ([@minimaxir](https://minimaxir.com))

*Max's open-source projects are supported by his [Patreon](https://www.patreon.com/minimaxir). If you found this project helpful, any monetary contributions to the Patreon are appreciated and will be put to good creative use.*

## License

MIT
