#include <Python.h>
#include <string>
#include "structmember.h"
#include "riak.pb.h"



static PyObject *
fastpb_convert5(::google::protobuf::int32 value)
{
    return PyLong_FromLong(value);
}

static PyObject *
fastpb_convert3(::google::protobuf::int64 value)
{
    return PyLong_FromLongLong(value);
}

static PyObject *
fastpb_convert18(::google::protobuf::int64 value)
{
    return PyLong_FromLongLong(value);
}

static PyObject *
fastpb_convert17(::google::protobuf::int32 value)
{
    return PyLong_FromLong(value);
}

static PyObject *
fastpb_convert13(::google::protobuf::uint32 value)
{
    return PyLong_FromUnsignedLong(value);
}

static PyObject *
fastpb_convert4(::google::protobuf::uint64 value)
{
    return PyLong_FromUnsignedLong(value);
}

static PyObject *
fastpb_convert1(double value)
{
    return PyFloat_FromDouble(value);
}

static PyObject *
fastpb_convert2(float value)
{
   return PyFloat_FromDouble(value);
}

static PyObject *
fastpb_convert9(const ::std::string &value)
{
    return PyUnicode_Decode(value.data(), value.length(), "utf-8", NULL);
}

static PyObject *
fastpb_convert12(const ::std::string &value)
{
    return PyString_FromStringAndSize(value.data(), value.length());
}

static PyObject *
fastpb_convert8(bool value)
{
    return PyBool_FromLong(value ? 1 : 0);
}

static PyObject *
fastpb_convert14(int value)
{
    // TODO(robbyw): Check EnumName_IsValid(value)
    return PyLong_FromLong(value);
}




  typedef struct {
      PyObject_HEAD

      riak_proto::RpbBucketProps *protobuf;
  } RpbBucketProps;

  static void
  RpbBucketProps_dealloc(RpbBucketProps* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbBucketProps_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbBucketProps *self;

      self = (RpbBucketProps *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbBucketProps();

      return (PyObject *)self;
  }

  static PyObject *
  RpbBucketProps_SerializeToString(RpbBucketProps* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbBucketProps_ParseFromString(RpbBucketProps* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbBucketProps_getn_val(RpbBucketProps *self, void *closure)
    {
        
          if (! self->protobuf->has_n_val()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->n_val());

        
    }

    static int
    RpbBucketProps_setn_val(RpbBucketProps *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_n_val();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The n_val attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_n_val(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbBucketProps_getallow_mult(RpbBucketProps *self, void *closure)
    {
        
          if (! self->protobuf->has_allow_mult()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->allow_mult());

        
    }

    static int
    RpbBucketProps_setallow_mult(RpbBucketProps *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_allow_mult();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The allow_mult attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_allow_mult(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbBucketProps_init(RpbBucketProps *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *n_val = NULL;
        
          PyObject *allow_mult = NULL;
        

        static char *kwlist[] = {
          
            (char *) "n_val",
          
            (char *) "allow_mult",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OO", kwlist,
            &n_val,&allow_mult))
          return -1;

        
          if (n_val) {
            if (RpbBucketProps_setn_val(self, n_val, NULL) < 0) {
              return -1;
            }
          }
        
          if (allow_mult) {
            if (RpbBucketProps_setallow_mult(self, allow_mult, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbBucketProps_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbBucketProps_getsetters[] = {
    
      {(char *)"n_val",
       (getter)RpbBucketProps_getn_val, (setter)RpbBucketProps_setn_val,
       (char *)"",
       NULL},
    
      {(char *)"allow_mult",
       (getter)RpbBucketProps_getallow_mult, (setter)RpbBucketProps_setallow_mult,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbBucketProps_methods[] = {
      {"SerializeToString", (PyCFunction)RpbBucketProps_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbBucketProps_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbBucketPropsType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbBucketProps",  /*tp_name*/
      sizeof(RpbBucketProps),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbBucketProps_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbBucketProps objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbBucketProps_methods,             /* tp_methods */
      RpbBucketProps_members,             /* tp_members */
      RpbBucketProps_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbBucketProps_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbBucketProps_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbDelReq *protobuf;
  } RpbDelReq;

  static void
  RpbDelReq_dealloc(RpbDelReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbDelReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbDelReq *self;

      self = (RpbDelReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbDelReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbDelReq_SerializeToString(RpbDelReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbDelReq_ParseFromString(RpbDelReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbDelReq_getbucket(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_bucket()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->bucket());

        
    }

    static int
    RpbDelReq_setbucket(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_bucket();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The bucket attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_bucket(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getkey(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_key()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->key());

        
    }

    static int
    RpbDelReq_setkey(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_key();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The key attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_key(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getrw(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_rw()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->rw());

        
    }

    static int
    RpbDelReq_setrw(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_rw();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The rw attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_rw(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getvclock(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_vclock()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->vclock());

        
    }

    static int
    RpbDelReq_setvclock(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_vclock();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The vclock attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_vclock(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getr(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_r()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->r());

        
    }

    static int
    RpbDelReq_setr(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_r();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The r attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_r(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getw(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_w()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->w());

        
    }

    static int
    RpbDelReq_setw(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_w();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The w attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_w(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getpr(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_pr()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->pr());

        
    }

    static int
    RpbDelReq_setpr(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_pr();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The pr attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_pr(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getpw(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_pw()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->pw());

        
    }

    static int
    RpbDelReq_setpw(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_pw();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The pw attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_pw(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbDelReq_getdw(RpbDelReq *self, void *closure)
    {
        
          if (! self->protobuf->has_dw()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->dw());

        
    }

    static int
    RpbDelReq_setdw(RpbDelReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_dw();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The dw attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_dw(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbDelReq_init(RpbDelReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *bucket = NULL;
        
          PyObject *key = NULL;
        
          PyObject *rw = NULL;
        
          PyObject *vclock = NULL;
        
          PyObject *r = NULL;
        
          PyObject *w = NULL;
        
          PyObject *pr = NULL;
        
          PyObject *pw = NULL;
        
          PyObject *dw = NULL;
        

        static char *kwlist[] = {
          
            (char *) "bucket",
          
            (char *) "key",
          
            (char *) "rw",
          
            (char *) "vclock",
          
            (char *) "r",
          
            (char *) "w",
          
            (char *) "pr",
          
            (char *) "pw",
          
            (char *) "dw",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOOOOOOOO", kwlist,
            &bucket,&key,&rw,&vclock,&r,&w,&pr,&pw,&dw))
          return -1;

        
          if (bucket) {
            if (RpbDelReq_setbucket(self, bucket, NULL) < 0) {
              return -1;
            }
          }
        
          if (key) {
            if (RpbDelReq_setkey(self, key, NULL) < 0) {
              return -1;
            }
          }
        
          if (rw) {
            if (RpbDelReq_setrw(self, rw, NULL) < 0) {
              return -1;
            }
          }
        
          if (vclock) {
            if (RpbDelReq_setvclock(self, vclock, NULL) < 0) {
              return -1;
            }
          }
        
          if (r) {
            if (RpbDelReq_setr(self, r, NULL) < 0) {
              return -1;
            }
          }
        
          if (w) {
            if (RpbDelReq_setw(self, w, NULL) < 0) {
              return -1;
            }
          }
        
          if (pr) {
            if (RpbDelReq_setpr(self, pr, NULL) < 0) {
              return -1;
            }
          }
        
          if (pw) {
            if (RpbDelReq_setpw(self, pw, NULL) < 0) {
              return -1;
            }
          }
        
          if (dw) {
            if (RpbDelReq_setdw(self, dw, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbDelReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbDelReq_getsetters[] = {
    
      {(char *)"bucket",
       (getter)RpbDelReq_getbucket, (setter)RpbDelReq_setbucket,
       (char *)"",
       NULL},
    
      {(char *)"key",
       (getter)RpbDelReq_getkey, (setter)RpbDelReq_setkey,
       (char *)"",
       NULL},
    
      {(char *)"rw",
       (getter)RpbDelReq_getrw, (setter)RpbDelReq_setrw,
       (char *)"",
       NULL},
    
      {(char *)"vclock",
       (getter)RpbDelReq_getvclock, (setter)RpbDelReq_setvclock,
       (char *)"",
       NULL},
    
      {(char *)"r",
       (getter)RpbDelReq_getr, (setter)RpbDelReq_setr,
       (char *)"",
       NULL},
    
      {(char *)"w",
       (getter)RpbDelReq_getw, (setter)RpbDelReq_setw,
       (char *)"",
       NULL},
    
      {(char *)"pr",
       (getter)RpbDelReq_getpr, (setter)RpbDelReq_setpr,
       (char *)"",
       NULL},
    
      {(char *)"pw",
       (getter)RpbDelReq_getpw, (setter)RpbDelReq_setpw,
       (char *)"",
       NULL},
    
      {(char *)"dw",
       (getter)RpbDelReq_getdw, (setter)RpbDelReq_setdw,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbDelReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbDelReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbDelReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbDelReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbDelReq",  /*tp_name*/
      sizeof(RpbDelReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbDelReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbDelReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbDelReq_methods,             /* tp_methods */
      RpbDelReq_members,             /* tp_members */
      RpbDelReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbDelReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbDelReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbErrorResp *protobuf;
  } RpbErrorResp;

  static void
  RpbErrorResp_dealloc(RpbErrorResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbErrorResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbErrorResp *self;

      self = (RpbErrorResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbErrorResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbErrorResp_SerializeToString(RpbErrorResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbErrorResp_ParseFromString(RpbErrorResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbErrorResp_geterrmsg(RpbErrorResp *self, void *closure)
    {
        
          if (! self->protobuf->has_errmsg()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->errmsg());

        
    }

    static int
    RpbErrorResp_seterrmsg(RpbErrorResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_errmsg();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The errmsg attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_errmsg(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbErrorResp_geterrcode(RpbErrorResp *self, void *closure)
    {
        
          if (! self->protobuf->has_errcode()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->errcode());

        
    }

    static int
    RpbErrorResp_seterrcode(RpbErrorResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_errcode();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The errcode attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_errcode(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbErrorResp_init(RpbErrorResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *errmsg = NULL;
        
          PyObject *errcode = NULL;
        

        static char *kwlist[] = {
          
            (char *) "errmsg",
          
            (char *) "errcode",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OO", kwlist,
            &errmsg,&errcode))
          return -1;

        
          if (errmsg) {
            if (RpbErrorResp_seterrmsg(self, errmsg, NULL) < 0) {
              return -1;
            }
          }
        
          if (errcode) {
            if (RpbErrorResp_seterrcode(self, errcode, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbErrorResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbErrorResp_getsetters[] = {
    
      {(char *)"errmsg",
       (getter)RpbErrorResp_geterrmsg, (setter)RpbErrorResp_seterrmsg,
       (char *)"",
       NULL},
    
      {(char *)"errcode",
       (getter)RpbErrorResp_geterrcode, (setter)RpbErrorResp_seterrcode,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbErrorResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbErrorResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbErrorResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbErrorRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbErrorResp",  /*tp_name*/
      sizeof(RpbErrorResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbErrorResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbErrorResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbErrorResp_methods,             /* tp_methods */
      RpbErrorResp_members,             /* tp_members */
      RpbErrorResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbErrorResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbErrorResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbGetBucketReq *protobuf;
  } RpbGetBucketReq;

  static void
  RpbGetBucketReq_dealloc(RpbGetBucketReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbGetBucketReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbGetBucketReq *self;

      self = (RpbGetBucketReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbGetBucketReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbGetBucketReq_SerializeToString(RpbGetBucketReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbGetBucketReq_ParseFromString(RpbGetBucketReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbGetBucketReq_getbucket(RpbGetBucketReq *self, void *closure)
    {
        
          if (! self->protobuf->has_bucket()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->bucket());

        
    }

    static int
    RpbGetBucketReq_setbucket(RpbGetBucketReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_bucket();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The bucket attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_bucket(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbGetBucketReq_init(RpbGetBucketReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *bucket = NULL;
        

        static char *kwlist[] = {
          
            (char *) "bucket",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &bucket))
          return -1;

        
          if (bucket) {
            if (RpbGetBucketReq_setbucket(self, bucket, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbGetBucketReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbGetBucketReq_getsetters[] = {
    
      {(char *)"bucket",
       (getter)RpbGetBucketReq_getbucket, (setter)RpbGetBucketReq_setbucket,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbGetBucketReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbGetBucketReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbGetBucketReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbGetBucketReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbGetBucketReq",  /*tp_name*/
      sizeof(RpbGetBucketReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbGetBucketReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbGetBucketReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbGetBucketReq_methods,             /* tp_methods */
      RpbGetBucketReq_members,             /* tp_members */
      RpbGetBucketReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbGetBucketReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbGetBucketReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbGetClientIdResp *protobuf;
  } RpbGetClientIdResp;

  static void
  RpbGetClientIdResp_dealloc(RpbGetClientIdResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbGetClientIdResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbGetClientIdResp *self;

      self = (RpbGetClientIdResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbGetClientIdResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbGetClientIdResp_SerializeToString(RpbGetClientIdResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbGetClientIdResp_ParseFromString(RpbGetClientIdResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbGetClientIdResp_getclient_id(RpbGetClientIdResp *self, void *closure)
    {
        
          if (! self->protobuf->has_client_id()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->client_id());

        
    }

    static int
    RpbGetClientIdResp_setclient_id(RpbGetClientIdResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_client_id();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The client_id attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_client_id(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbGetClientIdResp_init(RpbGetClientIdResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *client_id = NULL;
        

        static char *kwlist[] = {
          
            (char *) "client_id",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &client_id))
          return -1;

        
          if (client_id) {
            if (RpbGetClientIdResp_setclient_id(self, client_id, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbGetClientIdResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbGetClientIdResp_getsetters[] = {
    
      {(char *)"client_id",
       (getter)RpbGetClientIdResp_getclient_id, (setter)RpbGetClientIdResp_setclient_id,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbGetClientIdResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbGetClientIdResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbGetClientIdResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbGetClientIdRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbGetClientIdResp",  /*tp_name*/
      sizeof(RpbGetClientIdResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbGetClientIdResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbGetClientIdResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbGetClientIdResp_methods,             /* tp_methods */
      RpbGetClientIdResp_members,             /* tp_members */
      RpbGetClientIdResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbGetClientIdResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbGetClientIdResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbGetReq *protobuf;
  } RpbGetReq;

  static void
  RpbGetReq_dealloc(RpbGetReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbGetReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbGetReq *self;

      self = (RpbGetReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbGetReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbGetReq_SerializeToString(RpbGetReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbGetReq_ParseFromString(RpbGetReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbGetReq_getbucket(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_bucket()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->bucket());

        
    }

    static int
    RpbGetReq_setbucket(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_bucket();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The bucket attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_bucket(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_getkey(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_key()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->key());

        
    }

    static int
    RpbGetReq_setkey(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_key();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The key attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_key(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_getr(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_r()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->r());

        
    }

    static int
    RpbGetReq_setr(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_r();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The r attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_r(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_getpr(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_pr()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->pr());

        
    }

    static int
    RpbGetReq_setpr(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_pr();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The pr attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_pr(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_getbasic_quorum(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_basic_quorum()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->basic_quorum());

        
    }

    static int
    RpbGetReq_setbasic_quorum(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_basic_quorum();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The basic_quorum attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_basic_quorum(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_getnotfound_ok(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_notfound_ok()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->notfound_ok());

        
    }

    static int
    RpbGetReq_setnotfound_ok(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_notfound_ok();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The notfound_ok attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_notfound_ok(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_getif_modified(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_if_modified()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->if_modified());

        
    }

    static int
    RpbGetReq_setif_modified(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_if_modified();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The if_modified attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_if_modified(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_gethead(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_head()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->head());

        
    }

    static int
    RpbGetReq_sethead(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_head();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The head attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_head(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetReq_getdeletedvclock(RpbGetReq *self, void *closure)
    {
        
          if (! self->protobuf->has_deletedvclock()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->deletedvclock());

        
    }

    static int
    RpbGetReq_setdeletedvclock(RpbGetReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_deletedvclock();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The deletedvclock attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_deletedvclock(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbGetReq_init(RpbGetReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *bucket = NULL;
        
          PyObject *key = NULL;
        
          PyObject *r = NULL;
        
          PyObject *pr = NULL;
        
          PyObject *basic_quorum = NULL;
        
          PyObject *notfound_ok = NULL;
        
          PyObject *if_modified = NULL;
        
          PyObject *head = NULL;
        
          PyObject *deletedvclock = NULL;
        

        static char *kwlist[] = {
          
            (char *) "bucket",
          
            (char *) "key",
          
            (char *) "r",
          
            (char *) "pr",
          
            (char *) "basic_quorum",
          
            (char *) "notfound_ok",
          
            (char *) "if_modified",
          
            (char *) "head",
          
            (char *) "deletedvclock",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOOOOOOOO", kwlist,
            &bucket,&key,&r,&pr,&basic_quorum,&notfound_ok,&if_modified,&head,&deletedvclock))
          return -1;

        
          if (bucket) {
            if (RpbGetReq_setbucket(self, bucket, NULL) < 0) {
              return -1;
            }
          }
        
          if (key) {
            if (RpbGetReq_setkey(self, key, NULL) < 0) {
              return -1;
            }
          }
        
          if (r) {
            if (RpbGetReq_setr(self, r, NULL) < 0) {
              return -1;
            }
          }
        
          if (pr) {
            if (RpbGetReq_setpr(self, pr, NULL) < 0) {
              return -1;
            }
          }
        
          if (basic_quorum) {
            if (RpbGetReq_setbasic_quorum(self, basic_quorum, NULL) < 0) {
              return -1;
            }
          }
        
          if (notfound_ok) {
            if (RpbGetReq_setnotfound_ok(self, notfound_ok, NULL) < 0) {
              return -1;
            }
          }
        
          if (if_modified) {
            if (RpbGetReq_setif_modified(self, if_modified, NULL) < 0) {
              return -1;
            }
          }
        
          if (head) {
            if (RpbGetReq_sethead(self, head, NULL) < 0) {
              return -1;
            }
          }
        
          if (deletedvclock) {
            if (RpbGetReq_setdeletedvclock(self, deletedvclock, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbGetReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbGetReq_getsetters[] = {
    
      {(char *)"bucket",
       (getter)RpbGetReq_getbucket, (setter)RpbGetReq_setbucket,
       (char *)"",
       NULL},
    
      {(char *)"key",
       (getter)RpbGetReq_getkey, (setter)RpbGetReq_setkey,
       (char *)"",
       NULL},
    
      {(char *)"r",
       (getter)RpbGetReq_getr, (setter)RpbGetReq_setr,
       (char *)"",
       NULL},
    
      {(char *)"pr",
       (getter)RpbGetReq_getpr, (setter)RpbGetReq_setpr,
       (char *)"",
       NULL},
    
      {(char *)"basic_quorum",
       (getter)RpbGetReq_getbasic_quorum, (setter)RpbGetReq_setbasic_quorum,
       (char *)"",
       NULL},
    
      {(char *)"notfound_ok",
       (getter)RpbGetReq_getnotfound_ok, (setter)RpbGetReq_setnotfound_ok,
       (char *)"",
       NULL},
    
      {(char *)"if_modified",
       (getter)RpbGetReq_getif_modified, (setter)RpbGetReq_setif_modified,
       (char *)"",
       NULL},
    
      {(char *)"head",
       (getter)RpbGetReq_gethead, (setter)RpbGetReq_sethead,
       (char *)"",
       NULL},
    
      {(char *)"deletedvclock",
       (getter)RpbGetReq_getdeletedvclock, (setter)RpbGetReq_setdeletedvclock,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbGetReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbGetReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbGetReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbGetReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbGetReq",  /*tp_name*/
      sizeof(RpbGetReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbGetReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbGetReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbGetReq_methods,             /* tp_methods */
      RpbGetReq_members,             /* tp_members */
      RpbGetReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbGetReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbGetReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbGetServerInfoResp *protobuf;
  } RpbGetServerInfoResp;

  static void
  RpbGetServerInfoResp_dealloc(RpbGetServerInfoResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbGetServerInfoResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbGetServerInfoResp *self;

      self = (RpbGetServerInfoResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbGetServerInfoResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbGetServerInfoResp_SerializeToString(RpbGetServerInfoResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbGetServerInfoResp_ParseFromString(RpbGetServerInfoResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbGetServerInfoResp_getnode(RpbGetServerInfoResp *self, void *closure)
    {
        
          if (! self->protobuf->has_node()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->node());

        
    }

    static int
    RpbGetServerInfoResp_setnode(RpbGetServerInfoResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_node();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The node attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_node(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetServerInfoResp_getserver_version(RpbGetServerInfoResp *self, void *closure)
    {
        
          if (! self->protobuf->has_server_version()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->server_version());

        
    }

    static int
    RpbGetServerInfoResp_setserver_version(RpbGetServerInfoResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_server_version();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The server_version attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_server_version(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbGetServerInfoResp_init(RpbGetServerInfoResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *node = NULL;
        
          PyObject *server_version = NULL;
        

        static char *kwlist[] = {
          
            (char *) "node",
          
            (char *) "server_version",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OO", kwlist,
            &node,&server_version))
          return -1;

        
          if (node) {
            if (RpbGetServerInfoResp_setnode(self, node, NULL) < 0) {
              return -1;
            }
          }
        
          if (server_version) {
            if (RpbGetServerInfoResp_setserver_version(self, server_version, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbGetServerInfoResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbGetServerInfoResp_getsetters[] = {
    
      {(char *)"node",
       (getter)RpbGetServerInfoResp_getnode, (setter)RpbGetServerInfoResp_setnode,
       (char *)"",
       NULL},
    
      {(char *)"server_version",
       (getter)RpbGetServerInfoResp_getserver_version, (setter)RpbGetServerInfoResp_setserver_version,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbGetServerInfoResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbGetServerInfoResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbGetServerInfoResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbGetServerInfoRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbGetServerInfoResp",  /*tp_name*/
      sizeof(RpbGetServerInfoResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbGetServerInfoResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbGetServerInfoResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbGetServerInfoResp_methods,             /* tp_methods */
      RpbGetServerInfoResp_members,             /* tp_members */
      RpbGetServerInfoResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbGetServerInfoResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbGetServerInfoResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbLink *protobuf;
  } RpbLink;

  static void
  RpbLink_dealloc(RpbLink* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbLink_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbLink *self;

      self = (RpbLink *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbLink();

      return (PyObject *)self;
  }

  static PyObject *
  RpbLink_SerializeToString(RpbLink* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbLink_ParseFromString(RpbLink* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbLink_getbucket(RpbLink *self, void *closure)
    {
        
          if (! self->protobuf->has_bucket()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->bucket());

        
    }

    static int
    RpbLink_setbucket(RpbLink *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_bucket();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The bucket attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_bucket(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbLink_getkey(RpbLink *self, void *closure)
    {
        
          if (! self->protobuf->has_key()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->key());

        
    }

    static int
    RpbLink_setkey(RpbLink *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_key();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The key attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_key(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbLink_gettag(RpbLink *self, void *closure)
    {
        
          if (! self->protobuf->has_tag()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->tag());

        
    }

    static int
    RpbLink_settag(RpbLink *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_tag();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The tag attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_tag(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbLink_init(RpbLink *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *bucket = NULL;
        
          PyObject *key = NULL;
        
          PyObject *tag = NULL;
        

        static char *kwlist[] = {
          
            (char *) "bucket",
          
            (char *) "key",
          
            (char *) "tag",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOO", kwlist,
            &bucket,&key,&tag))
          return -1;

        
          if (bucket) {
            if (RpbLink_setbucket(self, bucket, NULL) < 0) {
              return -1;
            }
          }
        
          if (key) {
            if (RpbLink_setkey(self, key, NULL) < 0) {
              return -1;
            }
          }
        
          if (tag) {
            if (RpbLink_settag(self, tag, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbLink_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbLink_getsetters[] = {
    
      {(char *)"bucket",
       (getter)RpbLink_getbucket, (setter)RpbLink_setbucket,
       (char *)"",
       NULL},
    
      {(char *)"key",
       (getter)RpbLink_getkey, (setter)RpbLink_setkey,
       (char *)"",
       NULL},
    
      {(char *)"tag",
       (getter)RpbLink_gettag, (setter)RpbLink_settag,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbLink_methods[] = {
      {"SerializeToString", (PyCFunction)RpbLink_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbLink_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbLinkType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbLink",  /*tp_name*/
      sizeof(RpbLink),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbLink_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbLink objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbLink_methods,             /* tp_methods */
      RpbLink_members,             /* tp_members */
      RpbLink_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbLink_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbLink_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbListBucketsResp *protobuf;
  } RpbListBucketsResp;

  static void
  RpbListBucketsResp_dealloc(RpbListBucketsResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbListBucketsResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbListBucketsResp *self;

      self = (RpbListBucketsResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbListBucketsResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbListBucketsResp_SerializeToString(RpbListBucketsResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbListBucketsResp_ParseFromString(RpbListBucketsResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbListBucketsResp_getbuckets(RpbListBucketsResp *self, void *closure)
    {
        
          int len = self->protobuf->buckets_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert12(
                    self->protobuf->buckets(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    RpbListBucketsResp_setbuckets(RpbListBucketsResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_buckets();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The buckets attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The buckets attribute value must be a sequence");
        self->protobuf->clear_buckets();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The buckets attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
          
            self->protobuf->add_buckets(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  

  static int
  RpbListBucketsResp_init(RpbListBucketsResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *buckets = NULL;
        

        static char *kwlist[] = {
          
            (char *) "buckets",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &buckets))
          return -1;

        
          if (buckets) {
            if (RpbListBucketsResp_setbuckets(self, buckets, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbListBucketsResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbListBucketsResp_getsetters[] = {
    
      {(char *)"buckets",
       (getter)RpbListBucketsResp_getbuckets, (setter)RpbListBucketsResp_setbuckets,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbListBucketsResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbListBucketsResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbListBucketsResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbListBucketsRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbListBucketsResp",  /*tp_name*/
      sizeof(RpbListBucketsResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbListBucketsResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbListBucketsResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbListBucketsResp_methods,             /* tp_methods */
      RpbListBucketsResp_members,             /* tp_members */
      RpbListBucketsResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbListBucketsResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbListBucketsResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbListKeysReq *protobuf;
  } RpbListKeysReq;

  static void
  RpbListKeysReq_dealloc(RpbListKeysReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbListKeysReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbListKeysReq *self;

      self = (RpbListKeysReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbListKeysReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbListKeysReq_SerializeToString(RpbListKeysReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbListKeysReq_ParseFromString(RpbListKeysReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbListKeysReq_getbucket(RpbListKeysReq *self, void *closure)
    {
        
          if (! self->protobuf->has_bucket()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->bucket());

        
    }

    static int
    RpbListKeysReq_setbucket(RpbListKeysReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_bucket();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The bucket attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_bucket(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbListKeysReq_init(RpbListKeysReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *bucket = NULL;
        

        static char *kwlist[] = {
          
            (char *) "bucket",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &bucket))
          return -1;

        
          if (bucket) {
            if (RpbListKeysReq_setbucket(self, bucket, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbListKeysReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbListKeysReq_getsetters[] = {
    
      {(char *)"bucket",
       (getter)RpbListKeysReq_getbucket, (setter)RpbListKeysReq_setbucket,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbListKeysReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbListKeysReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbListKeysReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbListKeysReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbListKeysReq",  /*tp_name*/
      sizeof(RpbListKeysReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbListKeysReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbListKeysReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbListKeysReq_methods,             /* tp_methods */
      RpbListKeysReq_members,             /* tp_members */
      RpbListKeysReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbListKeysReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbListKeysReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbListKeysResp *protobuf;
  } RpbListKeysResp;

  static void
  RpbListKeysResp_dealloc(RpbListKeysResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbListKeysResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbListKeysResp *self;

      self = (RpbListKeysResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbListKeysResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbListKeysResp_SerializeToString(RpbListKeysResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbListKeysResp_ParseFromString(RpbListKeysResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbListKeysResp_getkeys(RpbListKeysResp *self, void *closure)
    {
        
          int len = self->protobuf->keys_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convert12(
                    self->protobuf->keys(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    RpbListKeysResp_setkeys(RpbListKeysResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_keys();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The keys attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The keys attribute value must be a sequence");
        self->protobuf->clear_keys();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The keys attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
          
            self->protobuf->add_keys(protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    RpbListKeysResp_getdone(RpbListKeysResp *self, void *closure)
    {
        
          if (! self->protobuf->has_done()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->done());

        
    }

    static int
    RpbListKeysResp_setdone(RpbListKeysResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_done();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The done attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_done(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbListKeysResp_init(RpbListKeysResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *keys = NULL;
        
          PyObject *done = NULL;
        

        static char *kwlist[] = {
          
            (char *) "keys",
          
            (char *) "done",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OO", kwlist,
            &keys,&done))
          return -1;

        
          if (keys) {
            if (RpbListKeysResp_setkeys(self, keys, NULL) < 0) {
              return -1;
            }
          }
        
          if (done) {
            if (RpbListKeysResp_setdone(self, done, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbListKeysResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbListKeysResp_getsetters[] = {
    
      {(char *)"keys",
       (getter)RpbListKeysResp_getkeys, (setter)RpbListKeysResp_setkeys,
       (char *)"",
       NULL},
    
      {(char *)"done",
       (getter)RpbListKeysResp_getdone, (setter)RpbListKeysResp_setdone,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbListKeysResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbListKeysResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbListKeysResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbListKeysRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbListKeysResp",  /*tp_name*/
      sizeof(RpbListKeysResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbListKeysResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbListKeysResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbListKeysResp_methods,             /* tp_methods */
      RpbListKeysResp_members,             /* tp_members */
      RpbListKeysResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbListKeysResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbListKeysResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbMapRedReq *protobuf;
  } RpbMapRedReq;

  static void
  RpbMapRedReq_dealloc(RpbMapRedReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbMapRedReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbMapRedReq *self;

      self = (RpbMapRedReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbMapRedReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbMapRedReq_SerializeToString(RpbMapRedReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbMapRedReq_ParseFromString(RpbMapRedReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbMapRedReq_getrequest(RpbMapRedReq *self, void *closure)
    {
        
          if (! self->protobuf->has_request()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->request());

        
    }

    static int
    RpbMapRedReq_setrequest(RpbMapRedReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_request();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The request attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_request(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbMapRedReq_getcontent_type(RpbMapRedReq *self, void *closure)
    {
        
          if (! self->protobuf->has_content_type()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->content_type());

        
    }

    static int
    RpbMapRedReq_setcontent_type(RpbMapRedReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_content_type();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The content_type attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_content_type(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbMapRedReq_init(RpbMapRedReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *request = NULL;
        
          PyObject *content_type = NULL;
        

        static char *kwlist[] = {
          
            (char *) "request",
          
            (char *) "content_type",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OO", kwlist,
            &request,&content_type))
          return -1;

        
          if (request) {
            if (RpbMapRedReq_setrequest(self, request, NULL) < 0) {
              return -1;
            }
          }
        
          if (content_type) {
            if (RpbMapRedReq_setcontent_type(self, content_type, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbMapRedReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbMapRedReq_getsetters[] = {
    
      {(char *)"request",
       (getter)RpbMapRedReq_getrequest, (setter)RpbMapRedReq_setrequest,
       (char *)"",
       NULL},
    
      {(char *)"content_type",
       (getter)RpbMapRedReq_getcontent_type, (setter)RpbMapRedReq_setcontent_type,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbMapRedReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbMapRedReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbMapRedReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbMapRedReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbMapRedReq",  /*tp_name*/
      sizeof(RpbMapRedReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbMapRedReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbMapRedReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbMapRedReq_methods,             /* tp_methods */
      RpbMapRedReq_members,             /* tp_members */
      RpbMapRedReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbMapRedReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbMapRedReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbMapRedResp *protobuf;
  } RpbMapRedResp;

  static void
  RpbMapRedResp_dealloc(RpbMapRedResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbMapRedResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbMapRedResp *self;

      self = (RpbMapRedResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbMapRedResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbMapRedResp_SerializeToString(RpbMapRedResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbMapRedResp_ParseFromString(RpbMapRedResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbMapRedResp_getphase(RpbMapRedResp *self, void *closure)
    {
        
          if (! self->protobuf->has_phase()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->phase());

        
    }

    static int
    RpbMapRedResp_setphase(RpbMapRedResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_phase();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The phase attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_phase(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbMapRedResp_getresponse(RpbMapRedResp *self, void *closure)
    {
        
          if (! self->protobuf->has_response()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->response());

        
    }

    static int
    RpbMapRedResp_setresponse(RpbMapRedResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_response();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The response attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_response(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbMapRedResp_getdone(RpbMapRedResp *self, void *closure)
    {
        
          if (! self->protobuf->has_done()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->done());

        
    }

    static int
    RpbMapRedResp_setdone(RpbMapRedResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_done();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The done attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_done(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbMapRedResp_init(RpbMapRedResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *phase = NULL;
        
          PyObject *response = NULL;
        
          PyObject *done = NULL;
        

        static char *kwlist[] = {
          
            (char *) "phase",
          
            (char *) "response",
          
            (char *) "done",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOO", kwlist,
            &phase,&response,&done))
          return -1;

        
          if (phase) {
            if (RpbMapRedResp_setphase(self, phase, NULL) < 0) {
              return -1;
            }
          }
        
          if (response) {
            if (RpbMapRedResp_setresponse(self, response, NULL) < 0) {
              return -1;
            }
          }
        
          if (done) {
            if (RpbMapRedResp_setdone(self, done, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbMapRedResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbMapRedResp_getsetters[] = {
    
      {(char *)"phase",
       (getter)RpbMapRedResp_getphase, (setter)RpbMapRedResp_setphase,
       (char *)"",
       NULL},
    
      {(char *)"response",
       (getter)RpbMapRedResp_getresponse, (setter)RpbMapRedResp_setresponse,
       (char *)"",
       NULL},
    
      {(char *)"done",
       (getter)RpbMapRedResp_getdone, (setter)RpbMapRedResp_setdone,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbMapRedResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbMapRedResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbMapRedResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbMapRedRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbMapRedResp",  /*tp_name*/
      sizeof(RpbMapRedResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbMapRedResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbMapRedResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbMapRedResp_methods,             /* tp_methods */
      RpbMapRedResp_members,             /* tp_members */
      RpbMapRedResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbMapRedResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbMapRedResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbPair *protobuf;
  } RpbPair;

  static void
  RpbPair_dealloc(RpbPair* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbPair_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbPair *self;

      self = (RpbPair *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbPair();

      return (PyObject *)self;
  }

  static PyObject *
  RpbPair_SerializeToString(RpbPair* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbPair_ParseFromString(RpbPair* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbPair_getkey(RpbPair *self, void *closure)
    {
        
          if (! self->protobuf->has_key()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->key());

        
    }

    static int
    RpbPair_setkey(RpbPair *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_key();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The key attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_key(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPair_getvalue(RpbPair *self, void *closure)
    {
        
          if (! self->protobuf->has_value()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->value());

        
    }

    static int
    RpbPair_setvalue(RpbPair *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_value();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The value attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_value(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbPair_init(RpbPair *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *key = NULL;
        
          PyObject *value = NULL;
        

        static char *kwlist[] = {
          
            (char *) "key",
          
            (char *) "value",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OO", kwlist,
            &key,&value))
          return -1;

        
          if (key) {
            if (RpbPair_setkey(self, key, NULL) < 0) {
              return -1;
            }
          }
        
          if (value) {
            if (RpbPair_setvalue(self, value, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbPair_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbPair_getsetters[] = {
    
      {(char *)"key",
       (getter)RpbPair_getkey, (setter)RpbPair_setkey,
       (char *)"",
       NULL},
    
      {(char *)"value",
       (getter)RpbPair_getvalue, (setter)RpbPair_setvalue,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbPair_methods[] = {
      {"SerializeToString", (PyCFunction)RpbPair_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbPair_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbPairType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbPair",  /*tp_name*/
      sizeof(RpbPair),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbPair_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbPair objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbPair_methods,             /* tp_methods */
      RpbPair_members,             /* tp_members */
      RpbPair_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbPair_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbPair_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbSetClientIdReq *protobuf;
  } RpbSetClientIdReq;

  static void
  RpbSetClientIdReq_dealloc(RpbSetClientIdReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbSetClientIdReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbSetClientIdReq *self;

      self = (RpbSetClientIdReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbSetClientIdReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbSetClientIdReq_SerializeToString(RpbSetClientIdReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbSetClientIdReq_ParseFromString(RpbSetClientIdReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbSetClientIdReq_getclient_id(RpbSetClientIdReq *self, void *closure)
    {
        
          if (! self->protobuf->has_client_id()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->client_id());

        
    }

    static int
    RpbSetClientIdReq_setclient_id(RpbSetClientIdReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_client_id();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The client_id attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_client_id(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbSetClientIdReq_init(RpbSetClientIdReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *client_id = NULL;
        

        static char *kwlist[] = {
          
            (char *) "client_id",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &client_id))
          return -1;

        
          if (client_id) {
            if (RpbSetClientIdReq_setclient_id(self, client_id, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbSetClientIdReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbSetClientIdReq_getsetters[] = {
    
      {(char *)"client_id",
       (getter)RpbSetClientIdReq_getclient_id, (setter)RpbSetClientIdReq_setclient_id,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbSetClientIdReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbSetClientIdReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbSetClientIdReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbSetClientIdReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbSetClientIdReq",  /*tp_name*/
      sizeof(RpbSetClientIdReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbSetClientIdReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbSetClientIdReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbSetClientIdReq_methods,             /* tp_methods */
      RpbSetClientIdReq_members,             /* tp_members */
      RpbSetClientIdReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbSetClientIdReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbSetClientIdReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbContent *protobuf;
  } RpbContent;

  static void
  RpbContent_dealloc(RpbContent* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbContent_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbContent *self;

      self = (RpbContent *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbContent();

      return (PyObject *)self;
  }

  static PyObject *
  RpbContent_SerializeToString(RpbContent* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbContent_ParseFromString(RpbContent* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbContent_getvalue(RpbContent *self, void *closure)
    {
        
          if (! self->protobuf->has_value()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->value());

        
    }

    static int
    RpbContent_setvalue(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_value();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The value attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_value(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbContent_getcontent_type(RpbContent *self, void *closure)
    {
        
          if (! self->protobuf->has_content_type()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->content_type());

        
    }

    static int
    RpbContent_setcontent_type(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_content_type();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The content_type attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_content_type(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbContent_getcharset(RpbContent *self, void *closure)
    {
        
          if (! self->protobuf->has_charset()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->charset());

        
    }

    static int
    RpbContent_setcharset(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_charset();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The charset attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_charset(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbContent_getcontent_encoding(RpbContent *self, void *closure)
    {
        
          if (! self->protobuf->has_content_encoding()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->content_encoding());

        
    }

    static int
    RpbContent_setcontent_encoding(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_content_encoding();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The content_encoding attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_content_encoding(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbContent_getvtag(RpbContent *self, void *closure)
    {
        
          if (! self->protobuf->has_vtag()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->vtag());

        
    }

    static int
    RpbContent_setvtag(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_vtag();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The vtag attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_vtag(protoValue);
        
      

      return 0;
    }
  
    
      static PyObject *
      fastpb_convertRpbContentlinks(const ::google::protobuf::Message &value)
      {
          RpbLink *obj = (RpbLink *)
              RpbLink_new(&RpbLinkType, NULL, NULL);
          obj->protobuf->MergeFrom(value);
          return (PyObject *)obj;
      }
    

    static PyObject *
    RpbContent_getlinks(RpbContent *self, void *closure)
    {
        
          int len = self->protobuf->links_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convertRpbContentlinks(
                    self->protobuf->links(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    RpbContent_setlinks(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_links();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The links attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The links attribute value must be a sequence");
        self->protobuf->clear_links();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      

        if (!PyType_IsSubtype(value->ob_type, &RpbLinkType)) {
          PyErr_SetString(PyExc_TypeError,
                          "The links attribute value must be an instance of RpbLink");
          return -1;
        }

         // .riak_proto.RpbLink
        ::riak_proto::RpbLink *protoValue =
            ((RpbLink *) value)->protobuf;

      

      
          
            self->protobuf->add_links()->MergeFrom(*protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    RpbContent_getlast_mod(RpbContent *self, void *closure)
    {
        
          if (! self->protobuf->has_last_mod()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->last_mod());

        
    }

    static int
    RpbContent_setlast_mod(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_last_mod();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The last_mod attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_last_mod(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbContent_getlast_mod_usecs(RpbContent *self, void *closure)
    {
        
          if (! self->protobuf->has_last_mod_usecs()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->last_mod_usecs());

        
    }

    static int
    RpbContent_setlast_mod_usecs(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_last_mod_usecs();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The last_mod_usecs attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_last_mod_usecs(protoValue);
        
      

      return 0;
    }
  
    
      static PyObject *
      fastpb_convertRpbContentusermeta(const ::google::protobuf::Message &value)
      {
          RpbPair *obj = (RpbPair *)
              RpbPair_new(&RpbPairType, NULL, NULL);
          obj->protobuf->MergeFrom(value);
          return (PyObject *)obj;
      }
    

    static PyObject *
    RpbContent_getusermeta(RpbContent *self, void *closure)
    {
        
          int len = self->protobuf->usermeta_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convertRpbContentusermeta(
                    self->protobuf->usermeta(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    RpbContent_setusermeta(RpbContent *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_usermeta();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The usermeta attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The usermeta attribute value must be a sequence");
        self->protobuf->clear_usermeta();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      

        if (!PyType_IsSubtype(value->ob_type, &RpbPairType)) {
          PyErr_SetString(PyExc_TypeError,
                          "The usermeta attribute value must be an instance of RpbPair");
          return -1;
        }

         // .riak_proto.RpbPair
        ::riak_proto::RpbPair *protoValue =
            ((RpbPair *) value)->protobuf;

      

      
          
            self->protobuf->add_usermeta()->MergeFrom(*protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  

  static int
  RpbContent_init(RpbContent *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *value = NULL;
        
          PyObject *content_type = NULL;
        
          PyObject *charset = NULL;
        
          PyObject *content_encoding = NULL;
        
          PyObject *vtag = NULL;
        
          PyObject *links = NULL;
        
          PyObject *last_mod = NULL;
        
          PyObject *last_mod_usecs = NULL;
        
          PyObject *usermeta = NULL;
        

        static char *kwlist[] = {
          
            (char *) "value",
          
            (char *) "content_type",
          
            (char *) "charset",
          
            (char *) "content_encoding",
          
            (char *) "vtag",
          
            (char *) "links",
          
            (char *) "last_mod",
          
            (char *) "last_mod_usecs",
          
            (char *) "usermeta",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOOOOOOOO", kwlist,
            &value,&content_type,&charset,&content_encoding,&vtag,&links,&last_mod,&last_mod_usecs,&usermeta))
          return -1;

        
          if (value) {
            if (RpbContent_setvalue(self, value, NULL) < 0) {
              return -1;
            }
          }
        
          if (content_type) {
            if (RpbContent_setcontent_type(self, content_type, NULL) < 0) {
              return -1;
            }
          }
        
          if (charset) {
            if (RpbContent_setcharset(self, charset, NULL) < 0) {
              return -1;
            }
          }
        
          if (content_encoding) {
            if (RpbContent_setcontent_encoding(self, content_encoding, NULL) < 0) {
              return -1;
            }
          }
        
          if (vtag) {
            if (RpbContent_setvtag(self, vtag, NULL) < 0) {
              return -1;
            }
          }
        
          if (links) {
            if (RpbContent_setlinks(self, links, NULL) < 0) {
              return -1;
            }
          }
        
          if (last_mod) {
            if (RpbContent_setlast_mod(self, last_mod, NULL) < 0) {
              return -1;
            }
          }
        
          if (last_mod_usecs) {
            if (RpbContent_setlast_mod_usecs(self, last_mod_usecs, NULL) < 0) {
              return -1;
            }
          }
        
          if (usermeta) {
            if (RpbContent_setusermeta(self, usermeta, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbContent_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbContent_getsetters[] = {
    
      {(char *)"value",
       (getter)RpbContent_getvalue, (setter)RpbContent_setvalue,
       (char *)"",
       NULL},
    
      {(char *)"content_type",
       (getter)RpbContent_getcontent_type, (setter)RpbContent_setcontent_type,
       (char *)"",
       NULL},
    
      {(char *)"charset",
       (getter)RpbContent_getcharset, (setter)RpbContent_setcharset,
       (char *)"",
       NULL},
    
      {(char *)"content_encoding",
       (getter)RpbContent_getcontent_encoding, (setter)RpbContent_setcontent_encoding,
       (char *)"",
       NULL},
    
      {(char *)"vtag",
       (getter)RpbContent_getvtag, (setter)RpbContent_setvtag,
       (char *)"",
       NULL},
    
      {(char *)"links",
       (getter)RpbContent_getlinks, (setter)RpbContent_setlinks,
       (char *)"",
       NULL},
    
      {(char *)"last_mod",
       (getter)RpbContent_getlast_mod, (setter)RpbContent_setlast_mod,
       (char *)"",
       NULL},
    
      {(char *)"last_mod_usecs",
       (getter)RpbContent_getlast_mod_usecs, (setter)RpbContent_setlast_mod_usecs,
       (char *)"",
       NULL},
    
      {(char *)"usermeta",
       (getter)RpbContent_getusermeta, (setter)RpbContent_setusermeta,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbContent_methods[] = {
      {"SerializeToString", (PyCFunction)RpbContent_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbContent_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbContentType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbContent",  /*tp_name*/
      sizeof(RpbContent),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbContent_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbContent objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbContent_methods,             /* tp_methods */
      RpbContent_members,             /* tp_members */
      RpbContent_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbContent_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbContent_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbGetBucketResp *protobuf;
  } RpbGetBucketResp;

  static void
  RpbGetBucketResp_dealloc(RpbGetBucketResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbGetBucketResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbGetBucketResp *self;

      self = (RpbGetBucketResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbGetBucketResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbGetBucketResp_SerializeToString(RpbGetBucketResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbGetBucketResp_ParseFromString(RpbGetBucketResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    
      static PyObject *
      fastpb_convertRpbGetBucketRespprops(const ::google::protobuf::Message &value)
      {
          RpbBucketProps *obj = (RpbBucketProps *)
              RpbBucketProps_new(&RpbBucketPropsType, NULL, NULL);
          obj->protobuf->MergeFrom(value);
          return (PyObject *)obj;
      }
    

    static PyObject *
    RpbGetBucketResp_getprops(RpbGetBucketResp *self, void *closure)
    {
        
          if (! self->protobuf->has_props()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convertRpbGetBucketRespprops(
                  self->protobuf->props());

        
    }

    static int
    RpbGetBucketResp_setprops(RpbGetBucketResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_props();
        return 0;
      }

      
        PyObject *value = input;
      

      

        if (!PyType_IsSubtype(value->ob_type, &RpbBucketPropsType)) {
          PyErr_SetString(PyExc_TypeError,
                          "The props attribute value must be an instance of RpbBucketProps");
          return -1;
        }

         // .riak_proto.RpbBucketProps
        ::riak_proto::RpbBucketProps *protoValue =
            ((RpbBucketProps *) value)->protobuf;

      

      
        
          self->protobuf->mutable_props()->MergeFrom(*protoValue);
        
      

      return 0;
    }
  

  static int
  RpbGetBucketResp_init(RpbGetBucketResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *props = NULL;
        

        static char *kwlist[] = {
          
            (char *) "props",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|O", kwlist,
            &props))
          return -1;

        
          if (props) {
            if (RpbGetBucketResp_setprops(self, props, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbGetBucketResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbGetBucketResp_getsetters[] = {
    
      {(char *)"props",
       (getter)RpbGetBucketResp_getprops, (setter)RpbGetBucketResp_setprops,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbGetBucketResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbGetBucketResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbGetBucketResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbGetBucketRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbGetBucketResp",  /*tp_name*/
      sizeof(RpbGetBucketResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbGetBucketResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbGetBucketResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbGetBucketResp_methods,             /* tp_methods */
      RpbGetBucketResp_members,             /* tp_members */
      RpbGetBucketResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbGetBucketResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbGetBucketResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbSetBucketReq *protobuf;
  } RpbSetBucketReq;

  static void
  RpbSetBucketReq_dealloc(RpbSetBucketReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbSetBucketReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbSetBucketReq *self;

      self = (RpbSetBucketReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbSetBucketReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbSetBucketReq_SerializeToString(RpbSetBucketReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbSetBucketReq_ParseFromString(RpbSetBucketReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbSetBucketReq_getbucket(RpbSetBucketReq *self, void *closure)
    {
        
          if (! self->protobuf->has_bucket()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->bucket());

        
    }

    static int
    RpbSetBucketReq_setbucket(RpbSetBucketReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_bucket();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The bucket attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_bucket(protoValue);
        
      

      return 0;
    }
  
    
      static PyObject *
      fastpb_convertRpbSetBucketReqprops(const ::google::protobuf::Message &value)
      {
          RpbBucketProps *obj = (RpbBucketProps *)
              RpbBucketProps_new(&RpbBucketPropsType, NULL, NULL);
          obj->protobuf->MergeFrom(value);
          return (PyObject *)obj;
      }
    

    static PyObject *
    RpbSetBucketReq_getprops(RpbSetBucketReq *self, void *closure)
    {
        
          if (! self->protobuf->has_props()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convertRpbSetBucketReqprops(
                  self->protobuf->props());

        
    }

    static int
    RpbSetBucketReq_setprops(RpbSetBucketReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_props();
        return 0;
      }

      
        PyObject *value = input;
      

      

        if (!PyType_IsSubtype(value->ob_type, &RpbBucketPropsType)) {
          PyErr_SetString(PyExc_TypeError,
                          "The props attribute value must be an instance of RpbBucketProps");
          return -1;
        }

         // .riak_proto.RpbBucketProps
        ::riak_proto::RpbBucketProps *protoValue =
            ((RpbBucketProps *) value)->protobuf;

      

      
        
          self->protobuf->mutable_props()->MergeFrom(*protoValue);
        
      

      return 0;
    }
  

  static int
  RpbSetBucketReq_init(RpbSetBucketReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *bucket = NULL;
        
          PyObject *props = NULL;
        

        static char *kwlist[] = {
          
            (char *) "bucket",
          
            (char *) "props",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OO", kwlist,
            &bucket,&props))
          return -1;

        
          if (bucket) {
            if (RpbSetBucketReq_setbucket(self, bucket, NULL) < 0) {
              return -1;
            }
          }
        
          if (props) {
            if (RpbSetBucketReq_setprops(self, props, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbSetBucketReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbSetBucketReq_getsetters[] = {
    
      {(char *)"bucket",
       (getter)RpbSetBucketReq_getbucket, (setter)RpbSetBucketReq_setbucket,
       (char *)"",
       NULL},
    
      {(char *)"props",
       (getter)RpbSetBucketReq_getprops, (setter)RpbSetBucketReq_setprops,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbSetBucketReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbSetBucketReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbSetBucketReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbSetBucketReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbSetBucketReq",  /*tp_name*/
      sizeof(RpbSetBucketReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbSetBucketReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbSetBucketReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbSetBucketReq_methods,             /* tp_methods */
      RpbSetBucketReq_members,             /* tp_members */
      RpbSetBucketReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbSetBucketReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbSetBucketReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbGetResp *protobuf;
  } RpbGetResp;

  static void
  RpbGetResp_dealloc(RpbGetResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbGetResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbGetResp *self;

      self = (RpbGetResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbGetResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbGetResp_SerializeToString(RpbGetResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbGetResp_ParseFromString(RpbGetResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    
      static PyObject *
      fastpb_convertRpbGetRespcontent(const ::google::protobuf::Message &value)
      {
          RpbContent *obj = (RpbContent *)
              RpbContent_new(&RpbContentType, NULL, NULL);
          obj->protobuf->MergeFrom(value);
          return (PyObject *)obj;
      }
    

    static PyObject *
    RpbGetResp_getcontent(RpbGetResp *self, void *closure)
    {
        
          int len = self->protobuf->content_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convertRpbGetRespcontent(
                    self->protobuf->content(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    RpbGetResp_setcontent(RpbGetResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_content();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The content attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The content attribute value must be a sequence");
        self->protobuf->clear_content();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      

        if (!PyType_IsSubtype(value->ob_type, &RpbContentType)) {
          PyErr_SetString(PyExc_TypeError,
                          "The content attribute value must be an instance of RpbContent");
          return -1;
        }

         // .riak_proto.RpbContent
        ::riak_proto::RpbContent *protoValue =
            ((RpbContent *) value)->protobuf;

      

      
          
            self->protobuf->add_content()->MergeFrom(*protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetResp_getvclock(RpbGetResp *self, void *closure)
    {
        
          if (! self->protobuf->has_vclock()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->vclock());

        
    }

    static int
    RpbGetResp_setvclock(RpbGetResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_vclock();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The vclock attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_vclock(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbGetResp_getunchanged(RpbGetResp *self, void *closure)
    {
        
          if (! self->protobuf->has_unchanged()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->unchanged());

        
    }

    static int
    RpbGetResp_setunchanged(RpbGetResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_unchanged();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The unchanged attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_unchanged(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbGetResp_init(RpbGetResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *content = NULL;
        
          PyObject *vclock = NULL;
        
          PyObject *unchanged = NULL;
        

        static char *kwlist[] = {
          
            (char *) "content",
          
            (char *) "vclock",
          
            (char *) "unchanged",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOO", kwlist,
            &content,&vclock,&unchanged))
          return -1;

        
          if (content) {
            if (RpbGetResp_setcontent(self, content, NULL) < 0) {
              return -1;
            }
          }
        
          if (vclock) {
            if (RpbGetResp_setvclock(self, vclock, NULL) < 0) {
              return -1;
            }
          }
        
          if (unchanged) {
            if (RpbGetResp_setunchanged(self, unchanged, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbGetResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbGetResp_getsetters[] = {
    
      {(char *)"content",
       (getter)RpbGetResp_getcontent, (setter)RpbGetResp_setcontent,
       (char *)"",
       NULL},
    
      {(char *)"vclock",
       (getter)RpbGetResp_getvclock, (setter)RpbGetResp_setvclock,
       (char *)"",
       NULL},
    
      {(char *)"unchanged",
       (getter)RpbGetResp_getunchanged, (setter)RpbGetResp_setunchanged,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbGetResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbGetResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbGetResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbGetRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbGetResp",  /*tp_name*/
      sizeof(RpbGetResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbGetResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbGetResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbGetResp_methods,             /* tp_methods */
      RpbGetResp_members,             /* tp_members */
      RpbGetResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbGetResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbGetResp_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbPutReq *protobuf;
  } RpbPutReq;

  static void
  RpbPutReq_dealloc(RpbPutReq* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbPutReq_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbPutReq *self;

      self = (RpbPutReq *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbPutReq();

      return (PyObject *)self;
  }

  static PyObject *
  RpbPutReq_SerializeToString(RpbPutReq* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbPutReq_ParseFromString(RpbPutReq* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    

    static PyObject *
    RpbPutReq_getbucket(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_bucket()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->bucket());

        
    }

    static int
    RpbPutReq_setbucket(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_bucket();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The bucket attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_bucket(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getkey(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_key()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->key());

        
    }

    static int
    RpbPutReq_setkey(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_key();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The key attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_key(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getvclock(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_vclock()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->vclock());

        
    }

    static int
    RpbPutReq_setvclock(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_vclock();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The vclock attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_vclock(protoValue);
        
      

      return 0;
    }
  
    
      static PyObject *
      fastpb_convertRpbPutReqcontent(const ::google::protobuf::Message &value)
      {
          RpbContent *obj = (RpbContent *)
              RpbContent_new(&RpbContentType, NULL, NULL);
          obj->protobuf->MergeFrom(value);
          return (PyObject *)obj;
      }
    

    static PyObject *
    RpbPutReq_getcontent(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_content()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convertRpbPutReqcontent(
                  self->protobuf->content());

        
    }

    static int
    RpbPutReq_setcontent(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_content();
        return 0;
      }

      
        PyObject *value = input;
      

      

        if (!PyType_IsSubtype(value->ob_type, &RpbContentType)) {
          PyErr_SetString(PyExc_TypeError,
                          "The content attribute value must be an instance of RpbContent");
          return -1;
        }

         // .riak_proto.RpbContent
        ::riak_proto::RpbContent *protoValue =
            ((RpbContent *) value)->protobuf;

      

      
        
          self->protobuf->mutable_content()->MergeFrom(*protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getw(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_w()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->w());

        
    }

    static int
    RpbPutReq_setw(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_w();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The w attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_w(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getdw(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_dw()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->dw());

        
    }

    static int
    RpbPutReq_setdw(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_dw();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The dw attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_dw(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getreturn_body(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_return_body()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->return_body());

        
    }

    static int
    RpbPutReq_setreturn_body(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_return_body();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The return_body attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_return_body(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getpw(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_pw()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert13(
                  self->protobuf->pw());

        
    }

    static int
    RpbPutReq_setpw(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_pw();
        return 0;
      }

      
        PyObject *value = input;
      

      
        
          ::google::protobuf::uint32 protoValue;
        

        // uint32
        if (PyInt_Check(value)) {
          protoValue = PyInt_AsUnsignedLongMask(value);
        } else if (PyLong_Check(value)) {
          protoValue = PyLong_AsUnsignedLong(value);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The pw attribute value must be an integer");
          return -1;
        }

      

      
        
          self->protobuf->set_pw(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getif_not_modified(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_if_not_modified()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->if_not_modified());

        
    }

    static int
    RpbPutReq_setif_not_modified(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_if_not_modified();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The if_not_modified attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_if_not_modified(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getif_none_match(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_if_none_match()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->if_none_match());

        
    }

    static int
    RpbPutReq_setif_none_match(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_if_none_match();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The if_none_match attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_if_none_match(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutReq_getreturn_head(RpbPutReq *self, void *closure)
    {
        
          if (! self->protobuf->has_return_head()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert8(
                  self->protobuf->return_head());

        
    }

    static int
    RpbPutReq_setreturn_head(RpbPutReq *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_return_head();
        return 0;
      }

      
        PyObject *value = input;
      

      
        bool protoValue;

        if (PyBool_Check(value)) {
          protoValue = (value == Py_True);
        } else {
          PyErr_SetString(PyExc_TypeError,
                          "The return_head attribute value must be a boolean");
          return -1;
        }

      

      
        
          self->protobuf->set_return_head(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbPutReq_init(RpbPutReq *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *bucket = NULL;
        
          PyObject *key = NULL;
        
          PyObject *vclock = NULL;
        
          PyObject *content = NULL;
        
          PyObject *w = NULL;
        
          PyObject *dw = NULL;
        
          PyObject *return_body = NULL;
        
          PyObject *pw = NULL;
        
          PyObject *if_not_modified = NULL;
        
          PyObject *if_none_match = NULL;
        
          PyObject *return_head = NULL;
        

        static char *kwlist[] = {
          
            (char *) "bucket",
          
            (char *) "key",
          
            (char *) "vclock",
          
            (char *) "content",
          
            (char *) "w",
          
            (char *) "dw",
          
            (char *) "return_body",
          
            (char *) "pw",
          
            (char *) "if_not_modified",
          
            (char *) "if_none_match",
          
            (char *) "return_head",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOOOOOOOOOO", kwlist,
            &bucket,&key,&vclock,&content,&w,&dw,&return_body,&pw,&if_not_modified,&if_none_match,&return_head))
          return -1;

        
          if (bucket) {
            if (RpbPutReq_setbucket(self, bucket, NULL) < 0) {
              return -1;
            }
          }
        
          if (key) {
            if (RpbPutReq_setkey(self, key, NULL) < 0) {
              return -1;
            }
          }
        
          if (vclock) {
            if (RpbPutReq_setvclock(self, vclock, NULL) < 0) {
              return -1;
            }
          }
        
          if (content) {
            if (RpbPutReq_setcontent(self, content, NULL) < 0) {
              return -1;
            }
          }
        
          if (w) {
            if (RpbPutReq_setw(self, w, NULL) < 0) {
              return -1;
            }
          }
        
          if (dw) {
            if (RpbPutReq_setdw(self, dw, NULL) < 0) {
              return -1;
            }
          }
        
          if (return_body) {
            if (RpbPutReq_setreturn_body(self, return_body, NULL) < 0) {
              return -1;
            }
          }
        
          if (pw) {
            if (RpbPutReq_setpw(self, pw, NULL) < 0) {
              return -1;
            }
          }
        
          if (if_not_modified) {
            if (RpbPutReq_setif_not_modified(self, if_not_modified, NULL) < 0) {
              return -1;
            }
          }
        
          if (if_none_match) {
            if (RpbPutReq_setif_none_match(self, if_none_match, NULL) < 0) {
              return -1;
            }
          }
        
          if (return_head) {
            if (RpbPutReq_setreturn_head(self, return_head, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbPutReq_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbPutReq_getsetters[] = {
    
      {(char *)"bucket",
       (getter)RpbPutReq_getbucket, (setter)RpbPutReq_setbucket,
       (char *)"",
       NULL},
    
      {(char *)"key",
       (getter)RpbPutReq_getkey, (setter)RpbPutReq_setkey,
       (char *)"",
       NULL},
    
      {(char *)"vclock",
       (getter)RpbPutReq_getvclock, (setter)RpbPutReq_setvclock,
       (char *)"",
       NULL},
    
      {(char *)"content",
       (getter)RpbPutReq_getcontent, (setter)RpbPutReq_setcontent,
       (char *)"",
       NULL},
    
      {(char *)"w",
       (getter)RpbPutReq_getw, (setter)RpbPutReq_setw,
       (char *)"",
       NULL},
    
      {(char *)"dw",
       (getter)RpbPutReq_getdw, (setter)RpbPutReq_setdw,
       (char *)"",
       NULL},
    
      {(char *)"return_body",
       (getter)RpbPutReq_getreturn_body, (setter)RpbPutReq_setreturn_body,
       (char *)"",
       NULL},
    
      {(char *)"pw",
       (getter)RpbPutReq_getpw, (setter)RpbPutReq_setpw,
       (char *)"",
       NULL},
    
      {(char *)"if_not_modified",
       (getter)RpbPutReq_getif_not_modified, (setter)RpbPutReq_setif_not_modified,
       (char *)"",
       NULL},
    
      {(char *)"if_none_match",
       (getter)RpbPutReq_getif_none_match, (setter)RpbPutReq_setif_none_match,
       (char *)"",
       NULL},
    
      {(char *)"return_head",
       (getter)RpbPutReq_getreturn_head, (setter)RpbPutReq_setreturn_head,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbPutReq_methods[] = {
      {"SerializeToString", (PyCFunction)RpbPutReq_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbPutReq_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbPutReqType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbPutReq",  /*tp_name*/
      sizeof(RpbPutReq),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbPutReq_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbPutReq objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbPutReq_methods,             /* tp_methods */
      RpbPutReq_members,             /* tp_members */
      RpbPutReq_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbPutReq_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbPutReq_new,                 /* tp_new */
  };


  typedef struct {
      PyObject_HEAD

      riak_proto::RpbPutResp *protobuf;
  } RpbPutResp;

  static void
  RpbPutResp_dealloc(RpbPutResp* self)
  {
      self->ob_type->tp_free((PyObject*)self);

      delete self->protobuf;
  }

  static PyObject *
  RpbPutResp_new(PyTypeObject *type, PyObject *args, PyObject *kwds)
  {
      RpbPutResp *self;

      self = (RpbPutResp *)type->tp_alloc(type, 0);

      self->protobuf = new riak_proto::RpbPutResp();

      return (PyObject *)self;
  }

  static PyObject *
  RpbPutResp_SerializeToString(RpbPutResp* self)
  {
      std::string result;
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->SerializeToString(&result);
      Py_END_ALLOW_THREADS
      return PyString_FromStringAndSize(result.data(), result.length());
  }


  static PyObject *
  RpbPutResp_ParseFromString(RpbPutResp* self, PyObject *value)
  {
      std::string serialized(PyString_AsString(value), PyString_Size(value));
      Py_BEGIN_ALLOW_THREADS
      self->protobuf->ParseFromString(serialized);
      Py_END_ALLOW_THREADS
      Py_RETURN_NONE;
  }


  
    
      static PyObject *
      fastpb_convertRpbPutRespcontent(const ::google::protobuf::Message &value)
      {
          RpbContent *obj = (RpbContent *)
              RpbContent_new(&RpbContentType, NULL, NULL);
          obj->protobuf->MergeFrom(value);
          return (PyObject *)obj;
      }
    

    static PyObject *
    RpbPutResp_getcontent(RpbPutResp *self, void *closure)
    {
        
          int len = self->protobuf->content_size();
          PyObject *tuple = PyTuple_New(len);
          for (int i = 0; i < len; ++i) {
            PyObject *value =
                fastpb_convertRpbPutRespcontent(
                    self->protobuf->content(i));
            PyTuple_SetItem(tuple, i, value);
          }
          return tuple;

        
    }

    static int
    RpbPutResp_setcontent(RpbPutResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_content();
        return 0;
      }

      
        if (PyString_Check(input)) {
          PyErr_SetString(PyExc_TypeError, "The content attribute value must be a sequence");
          return -1;
        }
        PyObject *sequence = PySequence_Fast(input, "The content attribute value must be a sequence");
        self->protobuf->clear_content();
        for (Py_ssize_t i = 0, len = PySequence_Length(sequence); i < len; ++i) {
          PyObject *value = PySequence_Fast_GET_ITEM(sequence, i);

      

      

        if (!PyType_IsSubtype(value->ob_type, &RpbContentType)) {
          PyErr_SetString(PyExc_TypeError,
                          "The content attribute value must be an instance of RpbContent");
          return -1;
        }

         // .riak_proto.RpbContent
        ::riak_proto::RpbContent *protoValue =
            ((RpbContent *) value)->protobuf;

      

      
          
            self->protobuf->add_content()->MergeFrom(*protoValue);
          
        }

        Py_XDECREF(sequence);
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutResp_getvclock(RpbPutResp *self, void *closure)
    {
        
          if (! self->protobuf->has_vclock()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->vclock());

        
    }

    static int
    RpbPutResp_setvclock(RpbPutResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_vclock();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The vclock attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_vclock(protoValue);
        
      

      return 0;
    }
  
    

    static PyObject *
    RpbPutResp_getkey(RpbPutResp *self, void *closure)
    {
        
          if (! self->protobuf->has_key()) {
            Py_RETURN_NONE;
          }

          return
              fastpb_convert12(
                  self->protobuf->key());

        
    }

    static int
    RpbPutResp_setkey(RpbPutResp *self, PyObject *input, void *closure)
    {
      if (input == NULL || input == Py_None) {
        self->protobuf->clear_key();
        return 0;
      }

      
        PyObject *value = input;
      

      
        // string
        if (! PyString_Check(value)) {
          PyErr_SetString(PyExc_TypeError, "The key attribute value must be a string");
          return -1;
        }

        std::string protoValue(PyString_AsString(value), PyString_Size(value));

      

      
        
          self->protobuf->set_key(protoValue);
        
      

      return 0;
    }
  

  static int
  RpbPutResp_init(RpbPutResp *self, PyObject *args, PyObject *kwds)
  {
      
        
          PyObject *content = NULL;
        
          PyObject *vclock = NULL;
        
          PyObject *key = NULL;
        

        static char *kwlist[] = {
          
            (char *) "content",
          
            (char *) "vclock",
          
            (char *) "key",
          
          NULL
        };

        if (! PyArg_ParseTupleAndKeywords(
            args, kwds, "|OOO", kwlist,
            &content,&vclock,&key))
          return -1;

        
          if (content) {
            if (RpbPutResp_setcontent(self, content, NULL) < 0) {
              return -1;
            }
          }
        
          if (vclock) {
            if (RpbPutResp_setvclock(self, vclock, NULL) < 0) {
              return -1;
            }
          }
        
          if (key) {
            if (RpbPutResp_setkey(self, key, NULL) < 0) {
              return -1;
            }
          }
        
      

      return 0;
  }

  static PyMemberDef RpbPutResp_members[] = {
      {NULL}  // Sentinel
  };


  static PyGetSetDef RpbPutResp_getsetters[] = {
    
      {(char *)"content",
       (getter)RpbPutResp_getcontent, (setter)RpbPutResp_setcontent,
       (char *)"",
       NULL},
    
      {(char *)"vclock",
       (getter)RpbPutResp_getvclock, (setter)RpbPutResp_setvclock,
       (char *)"",
       NULL},
    
      {(char *)"key",
       (getter)RpbPutResp_getkey, (setter)RpbPutResp_setkey,
       (char *)"",
       NULL},
    
      {NULL}  // Sentinel
  };


  static PyMethodDef RpbPutResp_methods[] = {
      {"SerializeToString", (PyCFunction)RpbPutResp_SerializeToString, METH_NOARGS,
       "Serializes the protocol buffer to a string."
      },
      {"ParseFromString", (PyCFunction)RpbPutResp_ParseFromString, METH_O,
       "Parses the protocol buffer from a string."
      },
      {NULL}  // Sentinel
  };


  static PyTypeObject RpbPutRespType = {
      PyObject_HEAD_INIT(NULL)
      0,                                      /*ob_size*/
      "riak_proto.RpbPutResp",  /*tp_name*/
      sizeof(RpbPutResp),             /*tp_basicsize*/
      0,                                      /*tp_itemsize*/
      (destructor)RpbPutResp_dealloc, /*tp_dealloc*/
      0,                                      /*tp_print*/
      0,                                      /*tp_getattr*/
      0,                                      /*tp_setattr*/
      0,                                      /*tp_compare*/
      0,                                      /*tp_repr*/
      0,                                      /*tp_as_number*/
      0,                                      /*tp_as_sequence*/
      0,                                      /*tp_as_mapping*/
      0,                                      /*tp_hash */
      0,                                      /*tp_call*/
      0,                                      /*tp_str*/
      0,                                      /*tp_getattro*/
      0,                                      /*tp_setattro*/
      0,                                      /*tp_as_buffer*/
      Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE, /*tp_flags*/
      "RpbPutResp objects",           /* tp_doc */
      0,                                      /* tp_traverse */
      0,                                      /* tp_clear */
      0,                   	 	                /* tp_richcompare */
      0,	   	                                /* tp_weaklistoffset */
      0,                   		                /* tp_iter */
      0,		                                  /* tp_iternext */
      RpbPutResp_methods,             /* tp_methods */
      RpbPutResp_members,             /* tp_members */
      RpbPutResp_getsetters,          /* tp_getset */
      0,                                      /* tp_base */
      0,                                      /* tp_dict */
      0,                                      /* tp_descr_get */
      0,                                      /* tp_descr_set */
      0,                                      /* tp_dictoffset */
      (initproc)RpbPutResp_init,      /* tp_init */
      0,                                      /* tp_alloc */
      RpbPutResp_new,                 /* tp_new */
  };



static PyMethodDef module_methods[] = {
    {NULL}  // Sentinel
};

#ifndef PyMODINIT_FUNC	// Declarations for DLL import/export.
#define PyMODINIT_FUNC void
#endif
PyMODINIT_FUNC
initriak_proto(void)
{
    GOOGLE_PROTOBUF_VERIFY_VERSION;

    PyObject* m;

    

    
      if (PyType_Ready(&RpbBucketPropsType) < 0)
          return;
    
      if (PyType_Ready(&RpbDelReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbErrorRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbGetBucketReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbGetClientIdRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbGetReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbGetServerInfoRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbLinkType) < 0)
          return;
    
      if (PyType_Ready(&RpbListBucketsRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbListKeysReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbListKeysRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbMapRedReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbMapRedRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbPairType) < 0)
          return;
    
      if (PyType_Ready(&RpbSetClientIdReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbContentType) < 0)
          return;
    
      if (PyType_Ready(&RpbGetBucketRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbSetBucketReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbGetRespType) < 0)
          return;
    
      if (PyType_Ready(&RpbPutReqType) < 0)
          return;
    
      if (PyType_Ready(&RpbPutRespType) < 0)
          return;
    

    m = Py_InitModule3("riak_proto", module_methods,
                       "");

    if (m == NULL)
      return;

    

    
      Py_INCREF(&RpbBucketPropsType);
      PyModule_AddObject(m, "RpbBucketProps", (PyObject *)&RpbBucketPropsType);
    
      Py_INCREF(&RpbDelReqType);
      PyModule_AddObject(m, "RpbDelReq", (PyObject *)&RpbDelReqType);
    
      Py_INCREF(&RpbErrorRespType);
      PyModule_AddObject(m, "RpbErrorResp", (PyObject *)&RpbErrorRespType);
    
      Py_INCREF(&RpbGetBucketReqType);
      PyModule_AddObject(m, "RpbGetBucketReq", (PyObject *)&RpbGetBucketReqType);
    
      Py_INCREF(&RpbGetClientIdRespType);
      PyModule_AddObject(m, "RpbGetClientIdResp", (PyObject *)&RpbGetClientIdRespType);
    
      Py_INCREF(&RpbGetReqType);
      PyModule_AddObject(m, "RpbGetReq", (PyObject *)&RpbGetReqType);
    
      Py_INCREF(&RpbGetServerInfoRespType);
      PyModule_AddObject(m, "RpbGetServerInfoResp", (PyObject *)&RpbGetServerInfoRespType);
    
      Py_INCREF(&RpbLinkType);
      PyModule_AddObject(m, "RpbLink", (PyObject *)&RpbLinkType);
    
      Py_INCREF(&RpbListBucketsRespType);
      PyModule_AddObject(m, "RpbListBucketsResp", (PyObject *)&RpbListBucketsRespType);
    
      Py_INCREF(&RpbListKeysReqType);
      PyModule_AddObject(m, "RpbListKeysReq", (PyObject *)&RpbListKeysReqType);
    
      Py_INCREF(&RpbListKeysRespType);
      PyModule_AddObject(m, "RpbListKeysResp", (PyObject *)&RpbListKeysRespType);
    
      Py_INCREF(&RpbMapRedReqType);
      PyModule_AddObject(m, "RpbMapRedReq", (PyObject *)&RpbMapRedReqType);
    
      Py_INCREF(&RpbMapRedRespType);
      PyModule_AddObject(m, "RpbMapRedResp", (PyObject *)&RpbMapRedRespType);
    
      Py_INCREF(&RpbPairType);
      PyModule_AddObject(m, "RpbPair", (PyObject *)&RpbPairType);
    
      Py_INCREF(&RpbSetClientIdReqType);
      PyModule_AddObject(m, "RpbSetClientIdReq", (PyObject *)&RpbSetClientIdReqType);
    
      Py_INCREF(&RpbContentType);
      PyModule_AddObject(m, "RpbContent", (PyObject *)&RpbContentType);
    
      Py_INCREF(&RpbGetBucketRespType);
      PyModule_AddObject(m, "RpbGetBucketResp", (PyObject *)&RpbGetBucketRespType);
    
      Py_INCREF(&RpbSetBucketReqType);
      PyModule_AddObject(m, "RpbSetBucketReq", (PyObject *)&RpbSetBucketReqType);
    
      Py_INCREF(&RpbGetRespType);
      PyModule_AddObject(m, "RpbGetResp", (PyObject *)&RpbGetRespType);
    
      Py_INCREF(&RpbPutReqType);
      PyModule_AddObject(m, "RpbPutReq", (PyObject *)&RpbPutReqType);
    
      Py_INCREF(&RpbPutRespType);
      PyModule_AddObject(m, "RpbPutResp", (PyObject *)&RpbPutRespType);
    
}