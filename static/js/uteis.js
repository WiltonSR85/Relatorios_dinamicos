export function rgbParaHex(rgb) {
    if (rgb.startsWith('#')) return rgb;
    const matches = rgb.match(/\d+/g);
    if (!matches) return '#000000';
    const [r, g, b] = matches;
    return '#' + [r, g, b].map(x => {
        const hex = parseInt(x).toString(16);
        return hex.length === 1 ? '0' + hex : hex;
    }).join('');
}