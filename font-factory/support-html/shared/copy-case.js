(function () {
  function titleCaseCopy(value) {
    let text = String(value ?? "");
    if (/^(?:ABCDEFGHIJKLM|NOPQRSTUVWXYZ)(?:\n(?:ABCDEFGHIJKLM|NOPQRSTUVWXYZ))*$/u.test(text)) {
      return text;
    }
    const urls = [];
    text = text.replace(/(?:https?:\/\/|www\.)[^\s]+/giu, (url) => {
      const marker = `\uE000${urls.length}\uE001`;
      urls.push(url);
      return marker;
    });
    text = text.replace(/\p{L}+(?:['’]\p{L}+)*/gu, (word) => {
      const initial = word.slice(0, 1).toLocaleUpperCase("en");
      const rest = word.slice(1);
      return initial + (word === word.toLocaleUpperCase("en")
        ? rest.toLocaleLowerCase("en") : rest);
    });
    return text.replace(/\uE000(\d+)\uE001/gu, (_match, index) => urls[Number(index)]);
  }

  window.supportTitleCase = titleCaseCopy;
})();
