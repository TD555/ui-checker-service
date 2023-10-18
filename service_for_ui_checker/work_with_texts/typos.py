import asyncio
from language_tool_python import LanguageTool
tool = LanguageTool('en')
from spellchecker import SpellChecker


class TypoCheck:
    def __init__(self, texts):
        self.texts = texts
        
    async def spellcheck_item(self, item):
        spell = SpellChecker()
        words = item['content'].split()

        typos = spell.unknown(words)
        
        corrected_typos = [{'typo' : typo, 'correct' : spell.correction(typo), "coords" : item} for typo in typos]

        return corrected_typos

    async def spell_checks(self):
        tasks = [self.spellcheck_item(item) for item in self.texts]
        results = await asyncio.gather(*tasks)

        filtered_results = [result for result in results if result]

        return filtered_results


    async def grammercheck_item(self, item): 

        matches = tool.check(item['content'])
        return [{'context' : matche.context, 'replacements' : matche.replacements, 'message' : matche.message, 'coords' : item} for matche in matches]


    async def grammar_checks(self):
        tasks = [self.grammercheck_item(item) for item in self.texts]
        results = await asyncio.gather(*tasks)
        data = []

        for result in results:
            data.extend(result)
        
        return data