/** gulpfile.js */
var gulp = require("gulp");
var browserify = require("browserify");
var source = require("vinyl-source-stream");
var browserSync = require("browser-sync");    // 今回追加したモジュール。変数名にはハイフンが使えないっぽい (後述)

/** 「gulp」コマンドを打たれた時に実行するコマンドたちを定義 */
gulp.task("default", ["watch", "build-js", "browserSync", "reload"]);

/** ファイルの更新をチェックして JS のビルド処理を呼び出す */
gulp.task("watch", () => {
  // () => は function() {} のショートハンド
  gulp.watch(["./src.js"], () => {
    gulp.start(["build-js"]);
  });
});

/** JS のビルド : src.js を main.js にビルドする */
gulp.task("build-js", () => {
  browserify({
    // ビルド対象ファイル
    entries: ["./src.js"]
  })
  .bundle()                   // Browserify の実行
  .pipe(source("main.js"))    // Vinyl に変換
  .pipe(gulp.dest("./"));     // 出力
});

/** ブラウザ表示 */
gulp.task("browserSync", () => {
  browserSync({
    server: {
      baseDir: "toeic-maker/"    // サーバとなる Root ディレクトリ
      ,index : "templates/my_page.html"
    }
  });
  // ファイルの監視 : 以下のファイルが変わったらリロード処理を呼び出す
  //gulp.watch("./main.js", ["reload"]); // ビルドされた JS ファイル
  gulp.watch("toeic-maker/templates/*.html",  ["reload"]); // HTML ファイル
  gulp.watch("toeic-maker/static/*css", ["reload"]);
});

/** リロード */
gulp.task("reload", () => {
  browserSync.reload();
});