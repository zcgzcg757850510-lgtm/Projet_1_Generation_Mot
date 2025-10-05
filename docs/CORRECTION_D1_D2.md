# 🔧 Correction du chargement automatique des fenêtres D1 et D2

## 🎯 Problème identifié (historique)
Les fenêtres A, B, C se chargeaient automatiquement, mais **D1 et D2** ne suivaient pas les bons fichiers et la logique de priorisation.

## 🔍 Analyse du problème

### Problème 1: Logique de détection des fichiers défaillante
**Fichier**: `web/services/files.py`

**Problème**: 
- Les fichiers D ont des noms comme `20250918-095045-941_靠_d1.svg` et `20250918-095045-941_靠_orig.svg`
- Mais la logique cherchait des fichiers finissant par `_靠.svg`
- Les variables `d0_mtime`, `d1_mtime`, `d2_mtime` n'étaient pas correctement initialisées
- La comparaison des timestamps était incorrecte

### Problème 2: Mapping fenêtre ↔ type backend et priorité
**Fichier**: `web/js/preview-manager.js`

**Problème**:
- Le mapping entre types backend et fenêtres UI n'était pas explicite
- La priorité de chargement D1 (préférée) vs D (fallback) n'était pas claire

## ✅ Solutions implémentées

### Solution 1: Correction de la détection des fichiers D
**Fichier**: `web/services/files.py`

```python
# Avant (BUGGY):
if not fn.endswith(suffix):  # Cherchait _靠.svg
    continue

# Après (CORRIGÉ):
if key == 'D':
    if f"_{ch}_" not in fn and not fn.endswith(f"_{ch}.svg"):
        continue  # Cherche _靠_ OU _靠.svg
```

**Améliorations**:
- ✅ Détection flexible des fichiers D avec `_靠_d1.svg`, `_靠_orig.svg`, etc.
- ✅ Variables `d0_mtime`, `d1_mtime`, `d2_mtime` correctement initialisées
- ✅ Comparaison des timestamps corrigée
- ✅ Stockage des noms de fichiers (pas des chemins complets)

### Solution 2: Amélioration du mapping et de la priorité de chargement
**Fichier**: `web/js/preview-manager.js`

```javascript
// Priorité D1 > D pour le chargement
if (files.D1) {
    console.log('🖼️ 加载D1图 (处理中轴):', files.D1);
    window.previewCardManager.setCardImage('D1', this.withTimestamp(`/D_processed_centerline/${files.D1}`));
    loadedCount++;
} else if (files.D) {
    console.log('🖼️ 加载D图 (处理中轴) 作为D1:', files.D);
    window.previewCardManager.setCardImage('D1', this.withTimestamp(`/D_processed_centerline/${files.D}`));
    loadedCount++;
}
```

**Améliorations**:
- ✅ Mapping UI clarifié (A→A, B→C, C→D1, D1→D2, D2→B)
- ✅ Priorité correcte: D1 en premier, puis D en fallback
- ✅ Gestion des deux systèmes (PreviewCardManager + DOM direct)
- ✅ Logging détaillé pour le débogage
- ✅ Chargement correct des fichiers D2

### Problème 3: Sémantique « D2 » ambiguë
- Bouton D2 (前端) = 中轴填充（Median Fill），输出 `D2_median_fill/` → UI窗口 B
- 兼容路径 D2 (/gen?type=D2) = 网格变形归档 `_d2.svg`，输出 `C_processed_centerline/`

### Solution 3: Documentation alignée
- WEB_INTERFACE.md 与 API_REFERENCE.md/D2_USAGE.md 已明确两条路径与UI映射

### Solution 3: Débogage et tests
**Ajouts**:
- ✅ Fonction `debugFileDetection()` globale
- ✅ Logging détaillé dans la console
- ✅ Page de test dédiée avec le caractère '靠'
- ✅ Messages informatifs dans la fenêtre de test

## 🧪 Tests de validation

### Test 1: Détection des fichiers
```bash
python -c "
from web.services.files import latest_filenames_for_char
result = latest_filenames_for_char('靠')
print(result)
"
```

**Résultat attendu**:
```
{
    'A': '20250918-095045-941_靠.svg',
    'B': '20250918-095045-941_靠.svg', 
    'C': '20250918-095045-941_靠.svg',
    'D': '20250918-095045-941_靠_d1.svg',
    'D0': '20250918-095045-941_靠_orig.svg',
    'D1': '20250918-095045-941_靠_d1.svg'
}
```

### Test 2: Interface utilisateur
1. Ouvrir `http://127.0.0.1:8766/`
2. Entrer le caractère '靠'
3. Les 4 fenêtres (A, B, C, D1) doivent se charger automatiquement

### Test 3: Page de test dédiée
1. Ouvrir `http://127.0.0.1:5000/test-auto-preview`
2. Cliquer sur "Tester le chargement automatique"
3. Vérifier que D1 et D2 se chargent correctement

## 📋 Résumé des fichiers modifiés

| Fichier | Modification | Status |
|---------|-------------|--------|
| `web/services/files.py` | ✅ Correction détection fichiers D | Corrigé |
| `web/js/preview-manager.js` | ✅ Amélioration logique chargement | Corrigé |
| `web/ui.html` | ✅ Ajout fonction débogage | Ajouté |
| `web/test-auto-preview.html` | ✅ Caractère de test '靠' | Mis à jour |

## 🎯 Résultat final

- A/B/C/D1/D2: chargement automatique et mapping corrigé
- Bouton D1: peut inclure `grid_state` → 结果显示在窗口 D2（来源：`D1_grid_transform/`）
- Bouton D2: 生成中轴填充 → 窗口 B（来源：`D2_median_fill/`）
- 兼容路径 D2: `_d2.svg` 归档（`C_processed_centerline/`）

