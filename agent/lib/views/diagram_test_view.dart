import 'package:flutter/material.dart';
import 'package:agent/widgets/mermaid_diagram.dart';

class DiagramTestView extends StatelessWidget {
  const DiagramTestView({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    const String flowchartExample = '''
    graph TD
      A[Start] --> B{Is it?}
      B -- Yes --> C[OK]
      C --> D[Rethink]
      D --> B
      B -- No ----> E[End]
    ''';

    const String sequenceDiagramExample = '''
    sequenceDiagram
      participant Alice
      participant Bob
      Alice->>John: Hello John, how are you?
      loop Healthcheck
          John->>John: Fight against hypochondria
      end
      Note right of John: Rational thoughts prevail!
      John-->>Alice: Great!
      John->>Bob: How about you?
      Bob-->>John: Jolly good!
    ''';

    return Scaffold(
      backgroundColor: Colors.black87,
      appBar: AppBar(
        title: const Text('Mermaid Diagram Examples'),
        backgroundColor: Colors.transparent,
        elevation: 0,
      ),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 1000),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Flowchart Example',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 24),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.1),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.2),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.all(24),
                  child: const MermaidDiagram(
                    diagramCode: flowchartExample,
                    width: 800,
                    height: 400,
                  ),
                ),
                const SizedBox(height: 48),
                const Text(
                  'Sequence Diagram Example',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                const SizedBox(height: 24),
                Container(
                  decoration: BoxDecoration(
                    color: Colors.white.withOpacity(0.05),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: Colors.white.withOpacity(0.1),
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.2),
                        blurRadius: 10,
                        offset: const Offset(0, 4),
                      ),
                    ],
                  ),
                  padding: const EdgeInsets.all(24),
                  child: const MermaidDiagram(
                    diagramCode: sequenceDiagramExample,
                    width: 800,
                    height: 500,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
