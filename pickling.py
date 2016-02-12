#! /usr/bin/python
import pickle

class TestClass:
	class_field = 0

	def get_class_field(self):
		return self.class_field

	def set_class_field(self, value):
		if isinstance(value, int):
			self.class_field = value
		else:
			raise Exception("The value must "
					"be of int type")

def main():
	t = TestClass()
	t.set_class_field(2)

	with open("/tmp/workfile", "wb") as f:
		pickle.dump(t, f)

	loaded_t = None
	with open("/tmp/workfile", "rb") as f:
		loaded_t = pickle.load(f)

	print("loaded_t fields [vars()]:")
	print(vars(loaded_t))
	print("loaded_t attributes [dir()]:")
	print(dir(loaded_t))

	print("the value of class is {0}"\
		.format(loaded_t.get_class_field()))

if __name__ == "__main__":
    main()
