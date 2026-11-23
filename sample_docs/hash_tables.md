# Hash Tables

A hash table stores key-value pairs and supports lookup, insertion and deletion
in O(1) average time. A hash function turns each key into an index in an array
of buckets.

## Collisions

Two different keys can hash to the same bucket. This is called a collision.
Hash tables handle collisions in two common ways:

- **Separate chaining:** each bucket holds a small list of entries. A collision
  just appends to the list.
- **Open addressing:** on a collision, probe other buckets (linear probing,
  quadratic probing or double hashing) until an empty slot is found.

## Load factor and resizing

The load factor is the number of entries divided by the number of buckets.
When the load factor gets too high, collisions become frequent and the table
is resized, usually doubling the bucket array and rehashing every key.

Python's `dict` and `set` are hash tables that use open addressing.
