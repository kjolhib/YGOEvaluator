# Yu-Gi-Oh Decision Evaluator — Storage Notes

## Card Information Format
Information regarding the cards are stored in a custom class that builds off of YGOPRODeck's own database. 

The raw card info will be fetched from https://db.ygoprodeck.com/api/v7/cardinfo.php (warning, visiting this website will load **all** cards that exists in the database), and only the relevant parts will be saved for use.

## JSON vs SQL/db
I will use simple JSON for storage.

The evaluator does not care about the entire cardpool, and so the simplest way is just JSON.
If and when this does expand too much, then I will consider moving it to a database that has format and card tables.