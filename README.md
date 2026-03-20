# premeth-data

Open-source collection of 2,600+ MCQ papers for MDCAT, AKU, NUMS, and other medical/engineering entry tests in Pakistan. Covers Biology, Chemistry, Physics, English, Logical Reasoning, and Computer Science.

## Structure

Each folder groups papers by source or purpose (e.g. `aku_papers/`, `subject_chemistry/`, `daily_tests/`). Every folder contains:

- **`index.json`** -- catalog of all papers in that folder
- **Question files** -- one `.json` per paper

### index.json

```json
{
  "papers": [
    {
      "id": "acids_bases_and_salts",
      "name": "Acids Bases And Salts",
      "subject": "Chemistry",
      "questionCount": 100,
      "topics": ["Acids, Bases and Salts"],
      "year": null
    }
  ]
}
```

The `id` matches the question filename (without `.json`).

### Question Files

```json
{
  "questions": [
    {
      "text": "All of the following are postulates of Arrhenius theory except",
      "image": null,
      "subject": "Chemistry",
      "topic": "Acids, Bases and Salts",
      "year": null,
      "options": [
        {
          "letter": "A",
          "text": "electrolytes ionize in water",
          "isCorrect": false,
          "explanation": "This is consistent with the Arrhenius theory."
        },
        {
          "letter": "B",
          "text": "ionization is a reversible process",
          "isCorrect": true,
          "explanation": "The Arrhenius theory does not address reversibility."
        }
      ],
      "explanation": "The Arrhenius theory does not address reversibility.",
      "explanationImage": null,
      "hints": []
    }
  ]
}
```

## Contributing

### Adding a New Paper

1. Pick the folder that best matches the paper's source or purpose
2. Create a snake_case `.json` file following the question schema above
3. Add an entry to that folder's `index.json` with a matching `id`
4. Open a pull request

### Improving Existing Data

- Fill in missing explanations, hints, subjects, topics, or years
- Fix incorrect answers or typos
- Make sure `questionCount` in `index.json` matches the actual question count

### Guidelines

- Follow the exact schema -- do not add or rename fields
- Every option needs its own explanation
- One paper per file
- Keep explanations clear enough for a student to understand *why* an answer is correct

## License

[MIT License](LICENSE)
