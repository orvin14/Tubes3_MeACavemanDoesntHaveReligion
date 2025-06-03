def generatePreProcessTable(pattern: str):
    badChar = {}
    for i in range(len(pattern)):
        badChar[pattern[i]] = i
    return badChar

def BM(text: str, pattern: str) -> int:
    count = 0
    patternLength = len(pattern)
    textLength = len(text)
    
    if patternLength == 0:
        return 0
    
    badChar = generatePreProcessTable(pattern)
    
    txtIdx = 0
    
    while txtIdx <= textLength - patternLength:
        patternIdx = patternLength - 1
        
        # Match from right to left
        while patternIdx >= 0 and text[txtIdx + patternIdx] == pattern[patternIdx]:
            patternIdx -= 1
        
        if patternIdx >= 0:
            # Mismatch occurred
            currChar = text[txtIdx + patternIdx]
    
            lastOccur = badChar.get(currChar, -1)
            shift = max(1, patternIdx - lastOccur)
            txtIdx += shift
        else:
            # Pattern found
            count += 1
            txtIdx += 1  
    
    return count
