# Sorting Algorithms

Sorting puts items in order. Many other algorithms, such as binary search,
need sorted input.

## Bubble sort
Repeatedly swaps adjacent items that are out of order. Simple but O(n^2).

## Merge sort
Merge sort is a divide and conquer algorithm. It splits the array in half,
sorts each half with a recursive call, then merges the two sorted halves.
Merge sort always runs in O(n log n) time and is stable, but needs O(n) extra
memory for merging.

## Quicksort
Quicksort picks a pivot, partitions the array into items smaller and larger
than the pivot, and sorts each part recursively. Its average time is
O(n log n), but a bad pivot choice gives O(n^2) in the worst case.

## Choosing an algorithm
For small arrays insertion sort is fast. For general use, merge sort or
quicksort. Python's built-in sort is Timsort, a hybrid of merge sort and
insertion sort.
