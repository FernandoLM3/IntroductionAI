# Tabla comparativa

## Pareja: Oradea - Urziceni

|Código| Path | Depth | Cost | Expanded | Status |
|-------|------|-----------|-----------|-----------|--------|
| Breadth First Search   |  Oradea → Sibiu → Fagaras → Bucharest → Urziceni  | 4 roads | 546 km | 8 nodes   |  |
| Uniform Cost Search   | Oradea → Sibiu → Rimnicu Vilcea → Pitesti → Bucharest → Urziceni | 5 roads | 514 km | 13 nodes |  |
| Depth First Search   | Oradea → Sibiu → Arad → Timisoara → Lugoj → Mehadia → Drobeta → Craiova → Pitesti → Bucharest → Urziceni | 10 roads | 1109 km | 11 nodes |  |
| Depth Limited Search | | | | 7 nodes | cutoff|
| Iterative Deepening Search   | Oradea → Sibiu → Fagaras → Bucharest → Urziceni | 4 roads  | 546 km | 18 nodes |   |

### ¿BFS encontró el camino con menos carreteras? ¿UCS el de menos km?
<body> </body>

### ¿Por qué DFS puede devolver un camino más largo aunque el grafo sea el mismo?
<body> </body>

### ¿Con qué --limit DLS pasó de cutoff a solución, y cómo se relaciona eso con la profundidad del camino de BFS/IDS?
<body> </body>

### Evidencias
#### Breadth First Search
![Breadth First Search](capturas/BreadthFirstSearch.png)