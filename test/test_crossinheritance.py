import py, os, sys
from pytest import raises
from .support import setup_make, pylong

currpath = py.path.local(__file__).dirpath()
test_dct = str(currpath.join("crossinheritanceDict"))

def setup_module(mod):
    setup_make("crossinheritance")


class TestCROSSINHERITANCE:
    def setup_class(cls):
        cls.test_dct = test_dct
        import cppyy
        cls.example01 = cppyy.load_reflection_info(cls.test_dct)

    def test01_override_function(self):
        """Test ability to override a simple function"""

        import cppyy
        Base1 = cppyy.gbl.CrossInheritance.Base1

        assert Base1().get_value() == 42

        class Derived(Base1):
            def get_value(self):
                return 13

        assert Derived().get_value() == 13

        assert 'Derived' in str(Derived())
        assert 'Derived' in repr(Derived())

        assert Base1.call_get_value(Base1())   == 42
        assert Base1.call_get_value(Derived()) == 13

    def test02_constructor(self):
        """Test constructor usage for derived classes"""

        import cppyy
        Base1 = cppyy.gbl.CrossInheritance.Base1

        assert Base1(27).get_value() == 27

        class Derived1(Base1):
            def __init__(self, pyval):
                Base1.__init__(self)
                self.m_pyint = pyval

            def get_value(self):
                return self.m_pyint+self.m_int

        d = Derived1(2)
        assert d.m_int   == 42
        assert d.m_pyint ==  2
        assert d.get_value()           == 44
        assert Base1.call_get_value(d) == 44

        class Derived2(Base1):
            def __init__(self, pyval, cppval):
                Base1.__init__(self, cppval)
                self.m_pyint = pyval

            def get_value(self):
                return self.m_pyint+self.m_int

        d = Derived2(2, 27)
        assert d.m_int   == 27
        assert d.m_pyint ==  2
        assert d.get_value()           == 29
        assert Base1.call_get_value(d) == 29

    def test03_override_function_abstract_base(self):
        """Test ability to override a simple function with an abstract base"""

        import cppyy
        CX = cppyy.gbl.CrossInheritance

        class C1PyBase2(CX.IBase2):
            def __init__(self):
                super(C1PyBase2, self).__init__()

            def get_value(self):
                return 99

        class C2PyBase2(CX.IBase2):
            def __init__(self):
                CX.IBase2.__init__(self)

            def get_value(self):
                return 91

        class C3PyBase2(CX.CBase2):
            def __init__(self):
                super(C3PyBase2, self).__init__()

        class C4PyBase2(CX.CBase2):
            def __init__(self):
                super(C4PyBase2, self).__init__()

            def get_value(self):
                return 13

        try:
            c2 = C2PyBase2()           # direct call to init can not work
            assert not "should have raised TypeError"
        except TypeError as e:
            assert "super" in str(e)   # clarifying message
            assert "abstract" in str(e)

        c1, c3, c4 = C1PyBase2(), C3PyBase2(), C4PyBase2()

        assert CX.IBase2.call_get_value(c1) == 99
        assert CX.IBase2.call_get_value(c3) == 42
        assert CX.IBase2.call_get_value(c4) == 13

        # now with abstract constructor that takes an argument
        class C4PyBase2(CX.IBase3):
            def __init__(self, intval):
                super(C4PyBase2, self).__init__(intval)

            def get_value(self):
                return 77

        c4 = C4PyBase2(88)
        assert c4.m_int == 88
        assert CX.IBase2.call_get_value(c4) == 77

    def test04_arguments(self):
        """Test ability to override functions that take arguments"""

        import cppyy
        Base1 = cppyy.gbl.CrossInheritance.Base1

        assert Base1(27).sum_value(-7) == 20

        class Derived1(Base1):
            def sum_value(self, val):
                return val + 13

        d1 = Derived1()
        assert d1.m_int   == 42
        assert d1.sum_value(-7)             == 6
        assert Base1.call_sum_value(d1, -7) == 6

        b1 = Base1()
        assert Base1.sum_pass_value(b1) == 6+2*b1.m_int

        class Derived2(Base1):
            def pass_value1(self, a):
                return a*2
            def pass_value2(self, a):
                return a.value*2
            def pass_value3(self, a):
                return a.value*2
            def pass_value4(self, b):
                return b.m_int*2
            def pass_value5(self, b):
                return b.m_int*2

        d2 = Derived2()
        assert Base1.sum_pass_value(d2) == 12+4*d2.m_int

    def test05_override_overloads(self):
        """Test ability to override overloaded functions"""

        import cppyy
        Base1 = cppyy.gbl.CrossInheritance.Base1

        assert Base1(27).sum_all(-7)     == 20
        assert Base1(27).sum_all(-3, -4) == 20

        class Derived(Base1):
            def sum_all(self, *args):
                return sum(args) + 13

        d = Derived()
        assert d.m_int   == 42
        assert d.sum_all(-7)             == 6
        assert Base1.call_sum_all(d, -7) == 6
        assert d.sum_all(-7, -5)             == 1
        assert Base1.call_sum_all(d, -7, -5) == 1

    def test06_const_methods(self):
        """Declared const methods should keep that qualifier"""

        import cppyy
        CX = cppyy.gbl.CrossInheritance

        class C1PyBase4(CX.IBase4):
            def __init__(self):
                super(C1PyBase4, self).__init__()

            def get_value(self):
                return 17

        class C2PyBase4(CX.CBase4):
            def __init__(self):
                super(C2PyBase4, self).__init__()

        c1, c2 = C1PyBase4(), C2PyBase4()

        assert CX.IBase4.call_get_value(c1) == 17
        assert CX.IBase4.call_get_value(c2) == 27

    def test07_templated_base(self):
        """Derive from a base class that is instantiated from a template"""

        import cppyy

        from cppyy.gbl.CrossInheritance import TBase1, TDerived1, TBase1_I

        class TPyDerived1(TBase1_I):
            def __init__(self):
                super(TBase1_I, self).__init__()

            def get_value(self):
                return 13

        b1, b2 = TBase1[int](), TBase1_I()
        assert b1.get_value() == 42
        assert b2.get_value() == 42

        d1 = TDerived1()
        assert d1.get_value() == 27

        p1 = TPyDerived1()
        assert p1.get_value() == 13

    def test08_error_handling(self):
        """Python errors should propagate through wrapper"""

        import cppyy
        Base1 = cppyy.gbl.CrossInheritance.Base1

        assert Base1(27).sum_value(-7) == 20

        errmsg = "I do not like the given value"
        class Derived(Base1):
            def sum_value(self, val):
                raise ValueError(errmsg)

        d = Derived()
        raises(ValueError, Base1.call_sum_value, d, -7)

        try:
            Base1.call_sum_value(d, -7)
            assert not "should not get here"
        except ValueError as e:
            assert errmsg in str(e)

    def test09_interface_checking(self):
        """Conversion errors should be Python exceptions"""

        import cppyy
        Base1 = cppyy.gbl.CrossInheritance.Base1

        assert Base1(27).sum_value(-7) == 20

        errmsg = "I do not like the given value"
        class Derived(Base1):
            def get_value(self):
                self.m_int*2       # missing return

        d = Derived(4)
        assert raises(TypeError, Base1.call_get_value, d)

    def test10_python_in_templates(self):
        """Usage of Python derived objects in std::vector"""

        import cppyy, gc

        CB = cppyy.gbl.CrossInheritance.CountableBase

        class PyCountable(CB):
            def call(self):
                try:
                    return self.extra + 42
                except AttributeError:
                    return 42

        start_count = CB.s_count

        v = cppyy.gbl.std.vector[PyCountable]()
        v.emplace_back(PyCountable())     # uses copy ctor
        assert len(v) == 1
        gc.collect()
        assert CB.s_count == 1 + start_count

        p = PyCountable()
        assert p.call() == 42
        p.extra = 42
        assert p.call() == 84
        v.emplace_back(p)
        assert len(v) == 2
        assert v[1].call() == 84          # copy ctor copies python state
        p.extra = 13
        assert p.call() == 55
        assert v[1].call() == 84
        del p
        gc.collect()
        assert CB.s_count == 2 + start_count

        v.push_back(PyCountable())        # uses copy ctor
        assert len(v) == 3
        gc.collect()
        assert CB.s_count == 3 + start_count

        del v
        gc.collect()
        assert CB.s_count == 0 + start_count

    def test11_python_in_make_shared(self):
        """Usage of Python derived objects with std::make_shared"""

        import cppyy

        cppyy.cppdef("""namespace MakeSharedTest {
        class Abstract {
        public:
          virtual ~Abstract() = 0;
          virtual int some_imp() = 0;
        };

        Abstract::~Abstract() {}

        int call_shared(std::shared_ptr<Abstract>& ptr) {
          return ptr->some_imp();
        } }""")

        from cppyy.gbl import std, MakeSharedTest
        from cppyy.gbl.MakeSharedTest import Abstract, call_shared

        class PyDerived(Abstract):
            def __init__(self, val):
                super(PyDerived, self).__init__()
                self.val = val
            def some_imp(self):
                return self.val

        v = std.make_shared[PyDerived](42)

        assert call_shared(v) == 42
        assert v.some_imp() == 42

        p = PyDerived(13)
        v = std.make_shared[PyDerived](p)
        assert call_shared(v) == 13
        assert v.some_imp() == 13

    def test12_python_shared_ptr_memory(self):
        """Usage of Python derived objects with std::shared_ptr"""

        import cppyy, gc

        std = cppyy.gbl.std
        CB  = cppyy.gbl.CrossInheritance.CountableBase

        class PyCountable(CB):
            def call(self):
                try:
                    return self.extra + 42
                except AttributeError:
                    return 42

        start_count = CB.s_count

        v = std.vector[std.shared_ptr[PyCountable]]()
        v.push_back(std.make_shared[PyCountable]())

        gc.collect()
        assert CB.s_count == 1 + start_count

        del v
        gc.collect()
        assert CB.s_count == 0 + start_count

    def test13_virtual_dtors_and_del(self):
        """Usage of virtual destructors and Python-side del."""

        import cppyy, warnings

        cppyy.cppdef("""namespace VirtualDtor {
        class MyClass1 {};    // no virtual dtor ...

        class MyClass2 {
        public:
          virtual ~MyClass2() {}
        };

        class MyClass3 : public MyClass2 {};

        template<class T>
        class MyClass4 {
        public:
          virtual ~MyClass4() {}
        }; }""")

        VD = cppyy.gbl.VirtualDtor

      # rethought this: just issue a warning if there is no virtual destructor
      # as the C++ side now carries the type of the dispatcher, not the type of
      # the direct base class
        with warnings.catch_warnings(record=True) as w:
            class MyPyDerived1(VD.MyClass1):
                pass        # TODO: verify warning is given
            assert len(w) == 1
            assert issubclass(w[-1].category, RuntimeWarning)
            assert "has no virtual destructor" in str(w[-1].message)

            d = MyPyDerived1()
            del d             # used to crash

        class MyPyDerived2(VD.MyClass2):
            pass

        d = MyPyDerived2()
        del d                 # used to crash

      # check a few more derivations that should not fail
        class MyPyDerived3(VD.MyClass3):
            pass

        class MyPyDerived4(VD.MyClass4[int]):
            pass

    def test14_protected_access(self):
        """Derived classes should have access to protected members"""

        import cppyy

        ns = cppyy.gbl.AccessProtected

        assert not 'my_data' in ns.MyBase.__dict__
        assert not hasattr(ns.MyBase(), 'my_data')

        class MyPyDerived(ns.MyBase):
            pass

        assert 'my_data' in MyPyDerived.__dict__
        assert MyPyDerived().my_data == 101

        class MyPyDerived(ns.MyBase):
            def __init__(self):
                super(MyPyDerived, self).__init__()
                assert self.my_data == 101
                self.py_data = 13
                self.my_data = 42

        m = MyPyDerived()
        assert m.py_data      == 13
        assert m.my_data      == 42
        assert m.get_data()   == 42
        assert m.get_data_v() == 42

    def test15_object_returns(self):
        """Return of C++ objects from overridden functions"""

        import cppyy

      # Part 1: return of a new C++ object
        cppyy.cppdef("""namespace object_returns {
        class Base {
        public:
          virtual Base* foo() { return new Base(); }
          virtual ~Base() {}
          virtual std::string whoami() { return "Base"; }
        };

        class CppDerived : public Base {
          CppDerived* foo() { return new CppDerived(); }
          ~CppDerived() {}
          virtual std::string whoami() { return "CppDerived"; }
        };

        Base* call_foo(Base& obj) { return obj.foo(); } }""")

        ns = cppyy.gbl.object_returns

        class PyDerived1(ns.Base):
            def foo(self):
                return ns.CppDerived()

        obj = PyDerived1()
        assert not ns.call_foo(obj)

        class PyDerived2(ns.Base):
            def foo(self):
                x = ns.CppDerived()
                x.__python_owns__ = False
                return x

        obj = PyDerived2()
        assert not not ns.call_foo(obj)

      # Part 2: return of a new Python derived object
        class PyDerived3(ns.Base):
            def foo(self):
                return PyDerived3()

            def whoami(self):
                return "PyDerived3"

        obj = PyDerived3()
        newobj = ns.call_foo(obj)
        assert not newobj

        class PyDerived4(ns.Base):
            def foo(self):
                d = PyDerived4()
                d.__python_owns__ = False
                d.alpha = 2
                return d

            def whoami(self):
                return "PyDerived4"

        obj = PyDerived4()
        new_obj = ns.call_foo(obj)
        assert not not new_obj
        assert new_obj.whoami() == "PyDerived4"

    def test16_cctor_access_controlled(self):
        """Python derived class of C++ class with access controlled cctor"""

        import cppyy

        cppyy.cppdef("""namespace cctor_access_controlled {
        class CommonBase {
        public:
          virtual ~CommonBase() {}
          virtual std::string whoami() = 0;
        };

        class Base1 : public CommonBase {
          Base1(const Base1&) {}
        public:
          Base1() {}
          virtual ~Base1() {}
          virtual std::string whoami() { return "Base1"; }
        };

        class Base2 : public CommonBase {
        protected:
          Base2(const Base2&) {}
        public:
          Base2() {}
          virtual ~Base2() {}
          virtual std::string whoami() { return "Base2"; }
        };

        std::string callit(CommonBase& obj) { return obj.whoami(); } }""")

        ns = cppyy.gbl.cctor_access_controlled

        for base in (ns.Base1, ns.Base2):
            class PyDerived(base):
                def whoami(self):
                    return "PyDerived"

            obj = PyDerived()
            assert ns.callit(obj) == "PyDerived"

    def test17_deep_hierarchy(self):
        """Test a deep Python hierarchy with pure virtual functions"""

        import cppyy

        cppyy.cppdef("""namespace deep_hierarchy {
        class Base {
        public:
          virtual ~Base() {}
          virtual std::string whoami() = 0;
        };

        std::string callit(Base& obj) { return obj.whoami(); } }""")

        ns = cppyy.gbl.deep_hierarchy

        class PyDerived1(ns.Base):
            def whoami(self):
                return "PyDerived1"

        obj = PyDerived1()
        assert ns.callit(obj) == "PyDerived1"

        class PyDerived2(PyDerived1):
            pass

        obj = PyDerived2()
        assert obj.whoami()   == "PyDerived1"
        assert ns.callit(obj) == "PyDerived1"

        class PyDerived3(PyDerived1):
            def whoami(self):
                return "PyDerived3"

        obj = PyDerived3()
        assert obj.whoami()   == "PyDerived3"
        assert ns.callit(obj) == "PyDerived3"

        class PyDerived4(PyDerived2):
            def whoami(self):
                return "PyDerived4"

        obj = PyDerived4()
        assert obj.whoami()   == "PyDerived4"
        assert ns.callit(obj) == "PyDerived4"

    def test18_abstract_hierarchy(self):
        """Hierarchy with abstract classes"""


        import cppyy

        cppyy.cppdef("""namespace abstract_classes {
        class Base {
        public:
          virtual ~Base() {}
          virtual std::string whoami()  = 0;
          virtual std::string message() = 0;
        };

        std::string whois(Base& obj) { return obj.whoami(); }
        std::string saywot(Base& obj) { return obj.message(); } }""")

        ns = cppyy.gbl.abstract_classes

        class PyDerived1(ns.Base):
            def __init__(self):
                super(PyDerived1, self).__init__()
                self._name = "PyDerived1"

            def whoami(self):
                return self._name

        class PyDerived2(PyDerived1):
            def __init__(self):
                super(PyDerived2, self).__init__()
                self._message = "Hello, World!"

            def message(self):
                return self._message

        obj = PyDerived2()
        assert obj.whoami()  == "PyDerived1"
        assert ns.whois(obj) == "PyDerived1"

        assert obj.message()  == "Hello, World!"
        assert ns.saywot(obj) == "Hello, World!"

    def test19_cpp_side_multiple_inheritance(self):
        """Hierarchy with multiple inheritance on the C++ side"""

        import cppyy

        cppyy.cppdef(""" namespace cpp_side_multiple_inheritance {
        struct Result {
          Result() : result(1337) {}
          Result(int r) : result(r) {}
          int result;
        };

        class Base1 {
        public:
          virtual ~Base1() {}
          virtual Result abstract1() = 0;
        };

        class Base2 {
        public:
          virtual ~Base2() {}
          virtual Result abstract2() = 0;
        };

        class Base : public Base1, public Base2 {
        public:
          Result abstract2() override { return Result(999); } 
        }; } """)

        ns = cppyy.gbl.cpp_side_multiple_inheritance

        class Derived(ns.Base):
            def abstract1(self):
                return ns.Result(1)

    def test20_basic_multiple_inheritance(self):
        """Basic multiple inheritance"""

        import cppyy

        cppyy.cppdef("""namespace basic_multiple_inheritance {
        class MyClass1 {
        public:
          MyClass1() : m_1(13) {}
          virtual ~MyClass1() {}
          virtual int x() = 0;

        public:
          int m_1;
        };
        int callx(MyClass1& m) { return m.x(); }

        class MyClass2 {
        public:
            MyClass2() : m_2(42) {}
            virtual ~MyClass2() {}
            virtual int y() = 0;

        public:
            int m_2;
        };
        int cally(MyClass2& m) { return m.y(); }

        class MyClass3 {
        public:
            MyClass3() : m_3(67) {}
            virtual ~MyClass3() {}
            virtual int z() = 0;

        public:
            int m_3;
        };
        int callz(MyClass3& m) { return m.z(); } }""")

        ns = cppyy.gbl.basic_multiple_inheritance

        class MyPyDerived(cppyy.multi(ns.MyClass1, ns.MyClass2)):
            def x(self):
                return 16

            def y(self):
                return 32

        assert len(MyPyDerived.__bases__) == 2

        a = MyPyDerived()
        assert a.x() == ns.callx(a)
        assert a.y() == ns.cally(a)

        assert a.m_1 == 13
        assert a.m_2 == 42

        class MyPyDerived2(cppyy.multi(ns.MyClass1, ns.MyClass2, ns.MyClass3)):
            def x(self):
                return 16

            def y(self):
                return 32

            def z(self):
                return 64

        assert len(MyPyDerived2.__bases__) == 3

        a = MyPyDerived2()
        assert a.x() == ns.callx(a)
        assert a.y() == ns.cally(a)
        assert a.z() == ns.callz(a)

        assert a.m_1 == 13
        assert a.m_2 == 42
        assert a.m_3 == 67

    def test21_multiple_inheritance_with_constructors(self):
        """Multiple inheritance with constructors"""

        import cppyy

        cppyy.cppdef("""namespace multiple_inheritance_with_constructors {
        class MyClass1 {
        public:
          MyClass1() : m_1(13) {}
          MyClass1(int i) : m_1(i) {}
          virtual ~MyClass1() {}
          virtual int x() = 0;

        public:
          int m_1;
        };
        int callx(MyClass1& m) { return m.x(); }

        class MyClass2 {
        public:
            MyClass2() : m_2(42) {}
            MyClass2(int i) : m_2(i) {}
            virtual ~MyClass2() {}
            virtual int y() = 0;

        public:
            int m_2;
        };
        int cally(MyClass2& m) { return m.y(); }

        class MyClass3 {
        public:
            MyClass3() : m_3(67) {}
            MyClass3(int i) : m_3(i) {}
            virtual ~MyClass3() {}
            virtual int z() = 0;

        public:
            int m_3;
        };
        int callz(MyClass3& m) { return m.z(); } }""")

        ns = cppyy.gbl.multiple_inheritance_with_constructors

        class MyPyDerived(cppyy.multi(ns.MyClass1, ns.MyClass2)):
            def __init__(self, val1, val2):
                super(MyPyDerived, self).__init__((val1,), (val2,))

            def x(self):
                return 16

            def y(self):
                return 32

        assert len(MyPyDerived.__bases__) == 2

        a = MyPyDerived(27, 88)
        assert a.x() == ns.callx(a)
        assert a.y() == ns.cally(a)

        assert a.m_1 == 27
        assert a.m_2 == 88

        class MyPyDerived2(cppyy.multi(ns.MyClass1, ns.MyClass2, ns.MyClass3)):
            def __init__(self, val1, val2, val3):
                super(MyPyDerived2, self).__init__((val1,), (val2,), (val3,))

            def x(self):
                return 16

            def y(self):
                return 32

            def z(self):
                return 64

        assert len(MyPyDerived2.__bases__) == 3

        a = MyPyDerived2(27, 88, -11)
        assert a.x() == ns.callx(a)
        assert a.y() == ns.cally(a)
        assert a.z() == ns.callz(a)

        assert a.m_1 ==  27
        assert a.m_2 ==  88
        assert a.m_3 == -11

    def test22_multiple_inheritance_with_defaults(self):
        """Multiple inheritance with defaults"""

        import cppyy

        cppyy.cppdef("""namespace multiple_inheritance_with_defaults {
        class MyClass1 {
        public:
          MyClass1(int i=13) : m_1(i) {}
          virtual ~MyClass1() {}
          virtual int x() = 0;

        public:
          int m_1;
        };
        int callx(MyClass1& m) { return m.x(); }

        class MyClass2 {
        public:
            MyClass2(int i=42) : m_2(i) {}
            virtual ~MyClass2() {}
            virtual int y() = 0;

        public:
            int m_2;
        };
        int cally(MyClass2& m) { return m.y(); }

        class MyClass3 {
        public:
            MyClass3(int i=67) : m_3(i) {}
            virtual ~MyClass3() {}
            virtual int z() = 0;

        public:
            int m_3;
        };
        int callz(MyClass3& m) { return m.z(); } }""")

        ns = cppyy.gbl.multiple_inheritance_with_defaults

        class MyPyDerived(cppyy.multi(ns.MyClass1, ns.MyClass2, ns.MyClass3)):
            def __init__(self, val1=None, val2=None, val3=None, nArgs=3):
                a1 = val1 is not None and (val1,) or ()
                a2 = val2 is not None and (val2,) or ()
                a3 = val3 is not None and (val3,) or ()
                if nArgs == 3:
                    super(MyPyDerived, self).__init__(a1, a2, a3)
                elif nArgs == 0:
                    super(MyPyDerived, self).__init__()
                elif nArgs == 1:
                    super(MyPyDerived, self).__init__(a1)
                elif nArgs == 2:
                    super(MyPyDerived, self).__init__(a1, a2)

            def x(self):
                return 16

            def y(self):
                return 32

            def z(self):
                return 64

        assert len(MyPyDerived.__bases__) == 3

        def verify(a, n1, n2, n3):
            assert a.m_1 == n1
            assert a.m_2 == n2
            assert a.m_3 == n3

        a = MyPyDerived(27, 88, -11)
        assert a.x() == ns.callx(a)
        assert a.y() == ns.cally(a)
        assert a.z() == ns.callz(a)

        verify(a, 27, 88, -11)

        a = MyPyDerived(val2=27)
        verify(a, 13, 27, 67)

        a = MyPyDerived(nArgs=0)
        verify(a, 13, 42, 67)

        a = MyPyDerived(27, nArgs=1)
        verify(a, 27, 42, 67)

        a = MyPyDerived(27, 55, nArgs=2)
        verify(a, 27, 55, 67)

    def test23_const_byvalue_return(self):
        """Const by-value return in overridden method"""

        import cppyy

        cppyy.cppdef("""namespace const_byvalue_return {
        struct Const {
            Const() = default;
            explicit Const(const std::string& s) { m_value = s; }
            std::string m_value;
        };

        struct Abstract {
            virtual ~Abstract() {}
            virtual const Const return_const() = 0;
        };

        const Const callit(Abstract* a) { return a->return_const(); } }""")

        ns = cppyy.gbl.const_byvalue_return

        class ReturnConstByValue(ns.Abstract):
             def return_const(self):
                 return ns.Const("abcdef")

        a = ReturnConstByValue()
        assert a.return_const().m_value == "abcdef"
        assert ns.callit(a).m_value     == "abcdef"

    def test24_non_copyable(self):
        """Inheriting from a non-copyable base class"""

        import cppyy

        cppyy.cppdef("""namespace non_copyable {
        struct Copyable {
            Copyable() = default;
            virtual ~Copyable() {}

            Copyable(const Copyable&) = default;
            Copyable& operator=(const Copyable&) = default;
        };

        struct Movable {
            Movable() = default;
            virtual ~Movable() {}

            Movable(const Movable&) = delete;
            Movable& operator=(const Movable&) = delete;
            Movable(Movable&&) = default;
            Movable& operator=(Movable&&) = default;
        }; }""")

        ns = cppyy.gbl.non_copyable

        Copyable = ns.Copyable
        Movable  = ns.Movable

        class DerivedCopyable(Copyable):
            pass

      # used to fail with compilation error
        class DerivedMovable(Movable):
            pass

      # used to fail with compilation error
        class DerivedMulti(cppyy.multi(Movable, Copyable)):
            pass

    def test25_default_ctor_and_multiple_inheritance(self):
        """Regression test: default ctor did not get added"""

        import cppyy

        cppyy.cppdef("""namespace default_ctor_and_multiple {
        struct Copyable {
            Copyable() = default;
            virtual ~Copyable() {}

            Copyable(const Copyable&) = default;
            Copyable& operator=(const Copyable&) = default;
        };

        struct Movable {
            Movable() = default;
            virtual ~Movable() {}

            Movable(const Movable&) = delete;
            Movable& operator=(const Movable&) = delete;
            Movable(Movable&&) = default;
            Movable& operator=(Movable&&) = default;
        };

        struct SomeClass {
            virtual ~SomeClass() {}
        }; }""")

        ns = cppyy.gbl.default_ctor_and_multiple
        Copyable  = ns.Copyable
        Movable   = ns.Movable
        SomeClass = ns.SomeClass

        class DerivedMulti(cppyy.multi(Movable, Copyable, SomeClass)):
            def __init__(self):
                super(DerivedMulti, self).__init__()

        d = DerivedMulti()
        assert d
