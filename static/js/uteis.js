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

export const fontes = [
    { valor: `"Segoe UI", Roboto, Helvetica, Arial, sans-serif`, nome: "Padrão (Sans-serif)" },
    { valor: `"Times New Roman", Times, serif`, nome: "Times New Roman" },
    { valor: `"Courier New", Courier, monospace`, nome: "Courier New" },
];

// objeto que mapeia tipos de dados do esquema para tipos de entrada HTML
export const tiposDeDadosEntrada = {
    'bool': 'text',
    'date': 'date',
    'datetime': 'datetime-local',
    'email': 'email',
    'float': 'number',
    'int': 'number',
    'number': 'number',
    'string': 'text',
};

export function formatarSQL(sql){
    let sqlFormatada = sql.replace(/\s+/g, " ").trim();

    const palavrasPrincipais = ["SELECT", "FROM", "WHERE", "GROUP BY", "ORDER BY", "LIMIT", "LEFT OUTER JOIN", "RIGHT OUTER JOIN", "INNER JOIN", "ON", "HAVING"];
    const palavrasSecundarias = ["AND", "OR", "AS", "DESC", "ASC", "IN", "IS", "NOT", "NULL", "LIKE", "BETWEEN", "EXISTS", "COUNT", "SUM", "AVG", "MIN", "MAX", "DISTINCT", "ESCAPE"];

    palavrasPrincipais.forEach(palavra => {
        const regex = new RegExp(`\\b${palavra}\\b`, "gi");
        sqlFormatada = sqlFormatada.replace(regex, 
            `</div><div class="text-primary font-weight-bold">${palavra}</div>
            <div class="text-dark pl-4">`
        );
    });

    palavrasSecundarias.forEach(palavra => {
        const regex = new RegExp(`\\b${palavra}\\b`, "gi");
        sqlFormatada = sqlFormatada.replace(regex, 
            `<span class="text-primary font-weight-bold">${palavra}</span>`
        );
    });

    sqlFormatada = sqlFormatada.replace("</div>", "");
    sqlFormatada += "</div>";                

    return sqlFormatada;
}