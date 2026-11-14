# Problem

Students, researchers, and anyone who keeps a large collection of notes, study materials, and documents on their computer often struggle to find what they need. As their folders grow, it becomes harder to remember which file contains a particular explanation, concept, or piece of information, especially when the same topic appears across multiple documents. Opening files individually takes too long, and basic file searches don't always make it easy to identify which results are most relevant or where the information appears. Some online search tools also require uploading personal documents or creating an account, which isn't ideal for people who want to keep their files private.

# Initial requirements

- R1: Allow users to select a local folder containing `.txt` and `.md` files and index their contents for searching.
- R2: Provide a clean, easy-to-use web interface where users can enter search queries and view results without needing an account.
- R3: Rank matching documents by relevance using a text-ranking algorithm, so the most useful results appear first rather than simply listing files alphabetically.
- R4: Display each result's file name and a short excerpt containing the matching text, so users can understand why the document appeared in their search results.
- R5: Highlight matching search terms within result snippets to make relevant information easier to identify.
- R6: Include a search evaluation page that measures ranking quality using Precision@k and Mean Reciprocal Rank (MRR) on a small, predefined set of test queries with known relevant documents.
- R7: Handle empty searches, folders with no supported documents, and queries with no matches by displaying clear, helpful messages instead of errors.
- R8: Keep all documents and the search index on the user's computer without uploading files or sending document contents to any external service.
