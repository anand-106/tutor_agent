import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:get/get.dart';
import 'dart:math' as math;

class FlashcardWidget extends StatefulWidget {
  final Map<String, dynamic> flashcardsData;
  final Function(Map<String, dynamic>)? onPinCard;
  final Function(List<Map<String, dynamic>>)? onPinAll;

  const FlashcardWidget({
    Key? key,
    required this.flashcardsData,
    this.onPinCard,
    this.onPinAll,
  }) : super(key: key);

  @override
  _FlashcardWidgetState createState() => _FlashcardWidgetState();
}

class _FlashcardWidgetState extends State<FlashcardWidget> {
  int currentIndex = 0;
  bool isFlipped = false;
  PageController pageController = PageController();
  List<bool> masteredCards = [];

  @override
  void initState() {
    super.initState();
    final flashcards = widget.flashcardsData['flashcards'] as List;
    masteredCards = List.generate(flashcards.length, (index) => false);
  }

  @override
  Widget build(BuildContext context) {
    final flashcards = widget.flashcardsData['flashcards'] as List;
    final topic = widget.flashcardsData['topic'] as String;
    final description = widget.flashcardsData['description'] as String;

    return Container(
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: Colors.white.withOpacity(0.08),
        ),
      ),
      padding: EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      topic,
                      style: GoogleFonts.inter(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        color: Theme.of(context).primaryColor,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      description,
                      style: GoogleFonts.inter(
                        fontSize: 14,
                        color: Colors.white.withOpacity(0.7),
                      ),
                    ),
                  ],
                ),
              ),
              IconButton(
                icon: Icon(Icons.push_pin_outlined),
                onPressed: () {
                  if (widget.onPinAll != null) {
                    widget
                        .onPinAll!(List<Map<String, dynamic>>.from(flashcards));
                  }
                },
                tooltip: 'Pin All Cards',
                color: Theme.of(context).primaryColor,
              ),
            ],
          ),
          SizedBox(height: 16),
          Container(
            height: 300,
            child: PageView.builder(
              controller: pageController,
              itemCount: flashcards.length,
              onPageChanged: (index) {
                setState(() {
                  currentIndex = index;
                  isFlipped = false;
                });
              },
              itemBuilder: (context, index) {
                final card = flashcards[index];
                return _buildFlashcard(card, index);
              },
            ),
          ),
          SizedBox(height: 16),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              IconButton(
                icon: Icon(Icons.arrow_back_ios),
                onPressed: currentIndex > 0
                    ? () {
                        pageController.previousPage(
                          duration: Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        );
                      }
                    : null,
                color: currentIndex > 0
                    ? Theme.of(context).primaryColor
                    : Colors.white.withOpacity(0.3),
              ),
              Row(
                children: [
                  Text(
                    '${currentIndex + 1}/${flashcards.length}',
                    style: GoogleFonts.inter(
                      fontSize: 14,
                      color: Colors.white.withOpacity(0.9),
                    ),
                  ),
                  SizedBox(width: 16),
                  IconButton(
                    icon: Icon(
                      (flashcards[currentIndex]['is_pinned'] as bool? ?? false)
                          ? Icons.push_pin
                          : Icons.push_pin_outlined,
                    ),
                    onPressed: () {
                      if (widget.onPinCard != null) {
                        final card =
                            Map<String, dynamic>.from(flashcards[currentIndex]);
                        final newPinState =
                            !(card['is_pinned'] as bool? ?? false);
                        debugPrint(
                            'Toggling pin state from ${card['is_pinned']} to $newPinState for card ID: ${card['id']}');
                        card['is_pinned'] = newPinState;
                        widget.onPinCard!(card);
                        setState(() {
                          flashcards[currentIndex]['is_pinned'] = newPinState;
                        });
                      }
                    },
                    tooltip: 'Pin Card',
                    color: (flashcards[currentIndex]['is_pinned'] as bool? ??
                            false)
                        ? Theme.of(context).primaryColor
                        : Colors.white.withOpacity(0.5),
                  ),
                ],
              ),
              IconButton(
                icon: Icon(Icons.arrow_forward_ios),
                onPressed: currentIndex < flashcards.length - 1
                    ? () {
                        pageController.nextPage(
                          duration: Duration(milliseconds: 300),
                          curve: Curves.easeInOut,
                        );
                      }
                    : null,
                color: currentIndex < flashcards.length - 1
                    ? Theme.of(context).primaryColor
                    : Colors.white.withOpacity(0.3),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildFlashcard(Map<String, dynamic> card, int index) {
    return GestureDetector(
      onTap: () {
        setState(() {
          isFlipped = !isFlipped;
        });
      },
      child: TweenAnimationBuilder(
        tween: Tween<double>(
          begin: isFlipped ? 0 : 180,
          end: isFlipped ? 180 : 0,
        ),
        duration: Duration(milliseconds: 300),
        builder: (context, double value, child) {
          var angle = value * math.pi / 180;
          return Transform(
            transform: Matrix4.identity()
              ..setEntry(3, 2, 0.001)
              ..rotateY(angle),
            alignment: Alignment.center,
            child: Container(
              margin: EdgeInsets.symmetric(horizontal: 16),
              child: angle < math.pi / 2
                  ? _buildCardSide(
                      card['front'],
                      card['category'],
                      card['importance'],
                      true,
                    )
                  : Transform(
                      transform: Matrix4.identity()..rotateY(math.pi),
                      alignment: Alignment.center,
                      child: _buildCardSide(
                        card['back'],
                        card['category'],
                        card['importance'],
                        false,
                      ),
                    ),
            ),
          );
        },
      ),
    );
  }

  Widget _buildCardSide(Map<String, dynamic> content, String category,
      String importance, bool isFront) {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: isFront
            ? Theme.of(context).primaryColor.withOpacity(0.1)
            : Colors.white.withOpacity(0.05),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isFront
              ? Theme.of(context).primaryColor.withOpacity(0.2)
              : Colors.white.withOpacity(0.08),
        ),
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Theme.of(context).primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  category,
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    color: Theme.of(context).primaryColor,
                  ),
                ),
              ),
              Container(
                padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: _getImportanceColor(importance).withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Text(
                  importance,
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    color: _getImportanceColor(importance),
                  ),
                ),
              ),
            ],
          ),
          SizedBox(height: 16),
          Text(
            content['title'],
            style: GoogleFonts.inter(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: Colors.white.withOpacity(0.9),
            ),
            textAlign: TextAlign.center,
          ),
          SizedBox(height: 16),
          Expanded(
            child: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  ...(content['points'] as List)
                      .map((point) => Padding(
                            padding: EdgeInsets.symmetric(vertical: 4),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '• ',
                                  style: GoogleFonts.inter(
                                    fontSize: 16,
                                    color: Theme.of(context).primaryColor,
                                  ),
                                ),
                                Expanded(
                                  child: Text(
                                    point.toString(),
                                    style: GoogleFonts.inter(
                                      fontSize: 16,
                                      color: Colors.white.withOpacity(0.9),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ))
                      .toList(),
                ],
              ),
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Tap to flip',
            style: GoogleFonts.inter(
              fontSize: 12,
              color: Colors.white.withOpacity(0.5),
            ),
          ),
        ],
      ),
    );
  }

  Color _getImportanceColor(String importance) {
    switch (importance.toLowerCase()) {
      case 'critical':
        return Colors.red;
      case 'important':
        return Colors.orange;
      case 'good to know':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }
}
