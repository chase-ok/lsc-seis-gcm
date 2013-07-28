
from gcm.utils import memoized, float_find_index
from gcm.data import make_data_path
import h5py
import numpy as np
from lockfile import LockBase, LockTimeout
from lockfile.mkdirlockfile import MkdirLockFile
from os.path import join
from functools import wraps
from collections import namedtuple
import time
import os
import inspect

LOCK_DIR = "/tmp/chase.kernan/"
LOCK_WRITE_TIMEOUT = 10.0
LOCK_READ_TIMEOUT = 5.0
LOCK_POLL = 0.01

use_locking = True

def _make_lock_path(name):
    return join(LOCK_DIR, name)

# TODO: working, but could use some clean-up
class ReadersWriterLock(object):

    def __init__(self, path, lock_class=MkdirLockFile):
        self.path = path
        self.waiting_lock = lock_class(path + "-waiting", threaded=False)
        self.about_to_write_lock = lock_class(path + "-about_to_write", threaded=False)
        self.write_lock = lock_class(path + "-write", threaded=False)
        self.num_readers_lock = lock_class(path + "-num_readers", threaded=False)
        self.read_lock = lock_class(path + "-read", threaded=False)
        self.num_readers_file = path + "-num_readers_{0}.txt"
        
    def break_lock(self):
        for lock in [self.waiting_lock, self.about_to_write_lock, 
                     self.write_lock, self.num_readers_lock]:
            lock.break_lock()
        for i in range(10):
            num_readers = self.num_readers_file.format(i)
            if os.path.exists(num_readers):
                os.remove(num_readers)

    def acquire_write(self):
        self.waiting_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)

        try:
            self._wait_on(self.num_readers_lock, LOCK_WRITE_TIMEOUT)
            self.read_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)
        except LockTimeout:
            self.waiting_lock.release()
            raise
        try:
            self.about_to_write_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)
        except LockTimeout:
            self.read_lock.release()
            self.waiting_lock.release()
            raise
        try:
            self.write_lock.acquire(timeout=LOCK_WRITE_TIMEOUT)
        except LockTimeout:
            self.about_to_write_lock.release()
            self.read_lock.release()
            self.waiting_lock.release()
            raise
        
        self.about_to_write_lock.release()

    def release_write(self):
        self.write_lock.release()
        self.read_lock.release()
        self.waiting_lock.release()

    def acquire_read(self):
        self._wait_on(self.waiting_lock, LOCK_READ_TIMEOUT)
        with self.waiting_lock:
            with self.num_readers_lock:
                self._local_file = self._get_local_num_readers_file()
                num_readers = self._get_local_num_readers(self._local_file) + 1
                self._set_local_num_readers(self._local_file, num_readers)

                if self._get_total_num_readers() == 1:
                    self.read_lock.acquire()
                    os.chmod(self.read_lock.lock_file, 0o777)

    def release_read(self):
        should_release_read = False
        with self.num_readers_lock:
            num_readers = self._get_local_num_readers(self._local_file) - 1
            self._set_local_num_readers(self._local_file, num_readers)
            if self._get_total_num_readers() == 0 \
                    and not self.about_to_write_lock.is_locked():
                self.read_lock.break_lock()

    # need to have multiple num_readers files so that cgi scripts and cluster
    # processes can both write to them. (Cluster processes can't write to the
    # CGI script num_readers and vice versa, but they can read from all)

    def _get_local_num_readers_file(self):
        for user in range(10):
            try:
                path = self.num_readers_file.format(user)
                with open(path, "a"): pass
                return path
            except IOError as e:
                if e.errno != 13:
                    self._create_num_readers(path)
                    return path

        raise ValueError("Too many users!")

    def _get_local_num_readers(self, file):
        with open(file, "r") as f:
            data = f.read()
        if data:
            return int(data)
        else:
            os.remove(file)
            self._create_num_readers(file)
            return 0

    def _get_total_num_readers(self):
        total = 0
        for user in range(10):
            try:
                with open(self.num_readers_file.format(user), "r") as f:
                    total += int(f.read())
            except IOError as e:
                return total
        raise ValueError("Too many users!")

    def _set_local_num_readers(self, file, num_readers):
        with open(file, "w") as f:
            f.write(str(num_readers))

    def _create_num_readers(self, file):
        handle = os.open(file, os.O_WRONLY|os.O_CREAT, 0o0777)
        os.fdopen(handle, 'w').close()
        with open(file, 'w') as f:
            f.write("0")

    def _wait_on(self, lock, timeout):
        end_time = time.time() + timeout
        while lock.is_locked():
            if time.time() > end_time:
                raise LockTimeout
            time.sleep(LOCK_POLL)


class _H5Store(object):
    
    _FileRecord = namedtuple('H5FileRecord', 'h5 accessors lock')
    _mode_map = {'r': 'r', 'w': 'a'}
    
    def __init__(self):
        self._readers = {}
        self._writers = {}
    
    def get_reader(self, name):
        return self._get(name, self._readers, 'r')
        
    def return_reader(self, name, h5):
        self._return(name, self._readers, h5, 'r')
        
    def get_writer(self, name):
        return self._get(name, self._writers, 'w')
        
    def return_writer(self, name, h5):
        self._return(name, self._writers, h5, 'w')
    
    def _get(self, name, records, mode):
        try:
            record = records[name]
        except KeyError:
            if use_locking:
                lock = ReadersWriterLock(_make_lock_path(name))
                if mode == 'w': 
                    lock.acquire_write()
                elif mode == 'r':
                    lock.acquire_read()
            else:
                lock = None
            
            h5 = h5py.File(make_data_path(name), mode=self._mode_map[mode])
            record = self._FileRecord(accessors=0, lock=lock, h5=h5)
        
        records[name] = record._replace(accessors=record.accessors+1)
        return record.h5
    
    def _return(self, name, records, h5, mode):
        record = records[name]
        assert record.h5 == h5
        
        num = record.accessors - 1
        if num == 0:
            if mode == 'w':
                record.h5.flush()
                record.h5.close()
                if record.lock: record.lock.release_write()
            elif mode == 'r':
                record.h5.close()
                if record.lock: record.lock.release_read()
            
            del records[name]
        else:
            records[name] = record._replace(accessors=num)
        
    def clear_locks(self):
        for records in [self._readers, self._writers]:
            for record in records.itervalues():
                if record.lock: record.lock.break_lock()
        self._readers.clear()
        self._writers.clear()

h5_store = _H5Store()
import atexit
atexit.register(h5_store.clear_locks)

class write_h5(object):

    def __init__(self, name, existing=None):
        self.name = name
        self.existing = existing
        # TODO: if existing check that it's writable?

    def __enter__(self):
        if self.existing is None:
            self.h5 = h5_store.get_writer(self.name)
        else:
            self.h5 = self.existing
        return self.h5

    def __exit__(self, type, value, traceback):
        if self.existing is None:
            h5_store.return_writer(self.name, self.h5)

class read_h5(object):

    def __init__(self, name, existing=None):
        self.name = name
        self.existing = existing
        
    def __enter__(self):
        if self.existing is None:
            self.h5 = h5_store.get_reader(self.name)
        else:
            self.h5 = self.existing
        return self.h5

    def __exit__(self, type, value, traceback):
        if self.existing is None:
            h5_store.return_reader(self.name, self.h5)


def open_group(h5, path):
    parts = path.split("/")
    for part in parts[:-1]:
        h5 = h5.require_group(part)
    return h5, parts[-1]


class use_h5(object):
    
    def __init__(self, h5_file, mode='r'):
        self.h5_file = h5_file
        self.mode = mode
        assert mode in ['r', 'w']
    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if 'h5' in kwargs and kwargs['h5'] is not None:
                if self.mode == 'w':
                    assert kwargs['h5'].file.mode in ['r+', 'w', 'w-', 'a'], \
                           "{0} needs a writable h5 file!".format(func)
                return func(*args, **kwargs)
            else:
                if self.mode == 'r':
                    method = read_h5(self.h5_file)
                elif self.mode == 'w':
                    method = write_h5(self.h5_file)
                
                with method as h5:
                    kwargs['h5'] = h5
                    return func(*args, **kwargs)
        return wrapper


class open_table(object):
    
    def __init__(self, h5_file, table, mode='r'):
        self.h5_file = h5_file
        self.table = table
        self.mode = mode
        assert mode in ['r', 'w']
    
    def __enter__(self):
        cls = (read_h5 if self.mode == 'r' else write_h5)
        self.h5_context = cls(self.h5_file)
        return self.table.attach(self.h5_context.__enter__())

    def __exit__(self, type, value, traceback):
        self.h5_context.__exit__(type, value, traceback)


class GenericTable(object):

    def __init__(self, path, 
                 dtype=[], chunk_size=100, compression='lzf', initial_size=0):
        # dtype should be a list of ('name', type) tuples
        self.path = path
        self.dtype = dtype
        self.row_class = namedtuple('TableRow', self.column_names)
        self.chunk_size = chunk_size
        self.compression = compression
        self.initial_size = initial_size

        self._h5 = None
        self._impl = None

    def attach(self, h5, reset=False):
        if not reset and self._h5 == h5:
            return self._impl

        group, self.name = open_group(h5, self.path)
        if reset and self.name in group: 
            del group[self.name]

        if self.name in group:
            dataset = group[self.name]
        else:
            dataset = group.require_dataset(name=self.name,
                                            shape=(self.initial_size,),
                                            dtype=self.dtype,
                                            chunks=(self.chunk_size,),
                                            maxshape=(None,),
                                            compression=self.compression,
                                            fletcher32=True,
                                            exact=False)

        self._impl = self.Implementation(self, dataset)
        self._h5 = h5
        return self._impl

    def make_row(self, **fields):
        return self.row_class(*(fields[col] for col in self.column_names))

    @property
    @memoized
    def column_names(self):
        return [field[0] for field in self.dtype]

    class Implementation(object):

        def __init__(self, meta, dataset):
            self._meta = meta
            self._row_class = meta.row_class
            self.dataset = dataset

            try:
                self._length
            except KeyError:
                self._length = 0

        @property
        def columns(self):
            class Columns(object):
                def __getattr__(inner, column):
                    return self.dataset[column][:len(self)]
            return Columns()

        @property
        def attrs(self):
            return self.dataset.attrs

        def read_dict(self, row_index):
            return self.read_row(row_index)._asdict()

        def read_row(self, row_index):
            if row_index >= self._length:
                raise IndexError
            if row_index < 0:
                if -row_index > self._length:
                    raise IndexError
                row_index += self._length
            return self._row_class(*self.dataset[row_index])

        def write_dict(self, row_index, **fields):
            self.write_row(row_index, self.make_row(**fields))

        def write_row(self, row_index, row):
            if row_index >= self._length:
                raise IndexError
            if row_index < 0:
                if -row_index > self._length:
                    raise IndexError
                row_index += self._length
            self.dataset[row_index] = row

        def append_dict(self, **fields):
            self.append_row(self.make_row(**fields))

        def append_row(self, row):
            index = self._get_next_index()
            self.dataset[index] = row
        
        def append_array(self, array):
            index = self._get_next_index()
            end = index + len(array)
            while end >= self.dataset.len():
                self._expand()
            
            self.dataset[index:end] = array
            self._length = end

        def iterdict(self):
            for i in range(len(self)):
                yield self.read_dict(i)

        def iterrows(self):
            for i in range(len(self)):
                yield self._row_class(*self.dataset[i])

        def __getitem__(self, key):
            if isinstance(key, slice):
                return [self.read_row(i) for i in 
                        xrange(*key.indices(len(self)))]
            else:
                return self.read_row(key)

        def __setitem__(self, key, item):
            if isinstance(key, slice):
                indices = range(*key.indices(len(self)))
                if np.iterable(item):
                    if len(item) != len(indices):
                        raise ValueError
                    for i, row in zip(indices, item):
                        self.write_row(i, row)
                else:
                    if indices[-1] >= self._length:
                        raise IndexError
                    self.dataset[indices] = item
            else:
                self.write_row(key, item)

        def __iter__(self):
            return self.iterrows()

        def __len__(self):
            return self._length

        def __getattr__(self, name):
            return getattr(self._meta, name)

        @property
        def _length(self):
            return self.dataset.attrs["length"]

        @_length.setter
        def _length(self, value):
            self.dataset.attrs["length"] = value

        def _get_next_index(self):
            index = self._length
            if index >= self.dataset.len():
                self._expand()
            self._length = index + 1
            return index
        
        def _expand(self):
            size = self.dataset.len()
            if size > 0:
                size *= 2
            else:
                size = 2**4
            self.dataset.resize((size,))
