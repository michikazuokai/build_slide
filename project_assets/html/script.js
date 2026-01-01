// JSONファイルの読み込み
fetch("data.json")
  .then(response => {
    console.log("✅ JSONレスポンス取得:", response);
    if (!response.ok) {
      throw new Error("❌ ネットワークエラー: " + response.status);
    }
    return response.json();
  })
  .then(data => {
    console.log("✅ JSONパース成功:", data);

    const gallery = document.getElementById("gallery");
    if (!gallery) {
      console.error("❌ #gallery 要素が見つかりません");
      return;
    }

    data.forEach((item, index) => {
      console.log(`🔍 item[${index}]:`, item);

      const figure = document.createElement("figure");

      const img = document.createElement("img");
      img.src = item.src;
      img.alt = item.alt;
      img.onerror = () => console.error(`❌ 画像読み込み失敗: ${img.src}`);

      const caption = document.createElement("figcaption");
      caption.textContent = item.caption;

      figure.appendChild(img);
      figure.appendChild(caption);
      gallery.appendChild(figure);
    });
  })
  .catch(error => {
    console.error("❌ JSON読み込みエラー:", error);
  });