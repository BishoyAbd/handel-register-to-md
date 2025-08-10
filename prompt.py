
PROMPT_COMPANY_NAME="""

I have a user-entered German company name: **[User Input Company Name]**.

Your task is to act as a data normalization and correction tool for the German Commercial Register (Handelsregister).

Based on the input, provide a JSON list of up to four most probable official company names.

Each JSON object in the list should contain two keys:
1.  `suggested_name`: The full, official name of the company, including its correct legal form (e.g., GmbH, AG, KG).
2.  `notes`: A brief explanation of why this name is a valid suggestion (e.g., a common abbreviation, a recent name change, a subsidiary, or a potential misspelling).

You must take into account:
-   Common misspellings and typos.
-   Abbreviations (e.g., "CCC" for "Competence Call Center").
-   Recent name changes or acquisitions (e.g., from 'Competence Call Center' to 'TELUS International Germany').
-   The correct legal form (e.g., the difference between GmbH and AG).
-   Subsidiaries or holding companies with similar names.

Do not provide more than four suggestions. The goal is to provide a highly focused and accurate list for data cleaning. Only provide the JSON output.
"""