# Big-O Notation

Big-O notation describes how the running time or memory of an algorithm grows
as the input size n grows. It ignores constant factors.

| Complexity | Name | Example |
|---|---|---|
| O(1) | constant | lookup in a hash table |
| O(log n) | logarithmic | binary search |
| O(n) | linear | scanning a list |
| O(n log n) | linearithmic | merge sort |
| O(n^2) | quadratic | bubble sort |

Best, average and worst case can differ: quicksort is O(n log n) on average
but O(n^2) in the worst case.
