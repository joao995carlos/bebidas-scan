import 'package:flutter/material.dart';

class LegalAcceptanceTile extends StatelessWidget {
  const LegalAcceptanceTile({
    super.key,
    required this.value,
    required this.onChanged,
    required this.title,
    required this.documentLabel,
    required this.onOpenDocument,
  });

  final bool value;
  final ValueChanged<bool?> onChanged;
  final String title;
  final String documentLabel;
  final VoidCallback onOpenDocument;

  @override
  Widget build(BuildContext context) {
    final colors = Theme.of(context).colorScheme;

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.fromLTRB(8, 8, 12, 8),
      decoration: BoxDecoration(
        color: const Color(0xfffffbf5),
        border: Border.all(
          color: value ? colors.primary : const Color(0xffead8c6),
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Checkbox(value: value, onChanged: onChanged),
          Expanded(
            child: Padding(
              padding: const EdgeInsets.only(top: 8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: const TextStyle(fontWeight: FontWeight.w700),
                  ),
                  const SizedBox(height: 6),
                  TextButton.icon(
                    onPressed: onOpenDocument,
                    icon: const Icon(Icons.open_in_new, size: 18),
                    label: Text(documentLabel),
                    style: TextButton.styleFrom(
                      padding: EdgeInsets.zero,
                      minimumSize: const Size(0, 36),
                      tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                      alignment: Alignment.centerLeft,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
