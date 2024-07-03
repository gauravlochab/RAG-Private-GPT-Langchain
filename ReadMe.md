# Private GPT

This is a codebase for a private GPT model. It includes various functionalities such as document ingestion, knowledge base creation, document personalization, document summarization, and more.

## Getting Started

To get started with this project, clone the repository and install the necessary dependencies.

## Structure

The codebase is structured as follows:

- `private_gpt`: The main package containing all the modules.
- `private_gpt/db`: Contains the database models and CRUD operations.
- `private_gpt/ingest`: Handles document ingestion.
- `private_gpt/knowledgebase.py`: Handles the creation of a new knowledge base.
- `private_gpt/blocks`: Contains various functionalities like document personalization and summarization.
- `private_gpt/chat`: Handles chat functionalities.
- `private_gpt/chunks`: Handles chunk retrieval.

## Usage

To use the functionalities provided by this codebase, you need to make API calls to the respective endpoints. For example, to create a new knowledge base, make a POST request to `/knowledge_bases`.

## Contributing

Contributions are welcome. Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)