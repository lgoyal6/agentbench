"""20 GSM8K-style math reasoning tasks.

Tasks are graded with ``exact`` scoring (with numeric fallback): the prediction
must contain the correct numeric answer. This is robust to chain-of-thought
outputs that end with "The answer is 42."
"""

from __future__ import annotations

from agentbench.suites.base import EvalSuite, EvalTask

_TASKS_RAW: list[tuple[str, str, str, str]] = [
    # (id, question, answer, difficulty)
    (
        "math-01",
        "Maria buys 3 boxes of pencils. Each box has 12 pencils. She gives 8 pencils to her brother. How many pencils does she have left?",
        "28",
        "easy",
    ),
    (
        "math-02",
        "A bus travels 60 miles per hour. How far does it travel in 2.5 hours?",
        "150",
        "easy",
    ),
    (
        "math-03",
        "Liam has $45. He spends $18 on a book and $7 on lunch. How much money does he have left?",
        "20",
        "easy",
    ),
    (
        "math-04",
        "A rectangle has length 9 cm and width 4 cm. What is its area in square centimeters?",
        "36",
        "easy",
    ),
    (
        "math-05",
        "There are 24 students in a class. One third of them play soccer. How many students play soccer?",
        "8",
        "easy",
    ),
    (
        "math-06",
        "A store sells apples for $0.75 each. Sam buys 12 apples and pays with a $20 bill. How much change does he get?",
        "11",
        "medium",
    ),
    (
        "math-07",
        "Train A leaves the station at 8:00 AM traveling 50 mph. Train B leaves the same station at 9:00 AM on the same track traveling 70 mph in the same direction. At what hour (in hours past 8:00 AM) does Train B catch Train A?",
        "3.5",
        "medium",
    ),
    (
        "math-08",
        "A water tank holds 240 liters when full. It is currently 5/8 full. How many liters of water are in it?",
        "150",
        "medium",
    ),
    (
        "math-09",
        "Jane's age is twice her brother Tim's age. In 5 years, the sum of their ages will be 40. How old is Jane now?",
        "20",
        "medium",
    ),
    (
        "math-10",
        "A bakery sold 84 muffins on Monday, twice as many on Tuesday, and 30 fewer on Wednesday than on Tuesday. How many muffins did it sell in total over the three days?",
        "390",
        "medium",
    ),
    (
        "math-11",
        "If 3 painters can paint 3 houses in 3 days, how many days will it take 5 painters to paint 5 houses (assuming each painter paints at the same rate as before)?",
        "3",
        "medium",
    ),
    (
        "math-12",
        "A car's gas tank holds 14 gallons and the car gets 32 miles per gallon. If the tank is currently 1/4 full, how many more miles can the car travel before running out of gas?",
        "112",
        "medium",
    ),
    (
        "math-13",
        "A shirt is on sale for 25% off its original price of $48. After the discount, an 8% sales tax is added. What is the final price in dollars (rounded to two decimals)?",
        "38.88",
        "medium",
    ),
    (
        "math-14",
        "If x + 2y = 14 and 3x - y = 7, what is the value of x?",
        "4",
        "medium",
    ),
    (
        "math-15",
        "A right triangle has legs of length 9 and 12. What is the length of the hypotenuse?",
        "15",
        "medium",
    ),
    (
        "math-16",
        "Alice invests $2000 at 5% simple annual interest. How much total money (principal plus interest) does she have after 3 years?",
        "2300",
        "hard",
    ),
    (
        "math-17",
        "A box contains 5 red marbles and 3 blue marbles. Two marbles are drawn without replacement. What is the probability (as a fraction) that both are red?",
        "5/14",
        "hard",
    ),
    (
        "math-18",
        "A school has 360 students. 60% are girls. Of the girls, 1/4 play sports. Of the boys, 2/3 play sports. How many students play sports?",
        "150",
        "hard",
    ),
    (
        "math-19",
        "A cylinder has radius 3 and height 10. Using pi = 3.14, what is its volume (rounded to the nearest integer)?",
        "283",
        "hard",
    ),
    (
        "math-20",
        "A father is 3 times as old as his son. 12 years ago, he was 9 times as old. How old is the son now?",
        "16",
        "hard",
    ),
]


math_reasoning_suite = EvalSuite(
    name="math_reasoning",
    version="0.1.0",
    description="20 GSM8K-style arithmetic and algebra word problems with numeric answers.",
    tasks=[
        EvalTask(
            id=tid,
            input={"question": q},
            expected_output=ans,
            difficulty=diff,  # type: ignore[arg-type]
            scorer_type="exact",
            metadata={"category": "math"},
        )
        for tid, q, ans, diff in _TASKS_RAW
    ],
)
