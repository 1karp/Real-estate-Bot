import unittest
from your_module import greeting  # Replace with the actual module and function name

class TestYourProject(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(greeting("Alice"), "Hey Alice")  # Adjust based on your implementation

if __name__ == '__main__':
    unittest.main()
